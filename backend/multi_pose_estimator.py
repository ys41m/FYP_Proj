"""
Multi-person pose estimation using YOLOv8-Pose with ByteTrack tracking.

Replaces MediaPipe single-person detection. Tracks two fighters simultaneously,
extracts per-fighter pose landmarks, and generates thumbnails for identification.
"""

import cv2
import numpy as np
import base64
from collections import Counter
from ultralytics import YOLO

from pose_estimator import (
    compute_boxing_angles, detect_stance, compute_frame_features,
    LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_ELBOW, RIGHT_ELBOW,
    LEFT_WRIST, RIGHT_WRIST, LEFT_HIP, RIGHT_HIP,
    LEFT_KNEE, RIGHT_KNEE, LEFT_ANKLE, RIGHT_ANKLE, NOSE,
)

# COCO 17 keypoints -> MediaPipe 33 landmark indices
# COCO: nose(0), left_eye(1), right_eye(2), left_ear(3), right_ear(4),
#        left_shoulder(5), right_shoulder(6), left_elbow(7), right_elbow(8),
#        left_wrist(9), right_wrist(10), left_hip(11), right_hip(12),
#        left_knee(13), right_knee(14), left_ankle(15), right_ankle(16)
COCO_TO_MP = {
    0: 0,    # nose -> nose
    1: 2,    # left_eye -> left_eye (MP index 2)
    2: 5,    # right_eye -> right_eye (MP index 5)
    3: 7,    # left_ear -> left_ear
    4: 8,    # right_ear -> right_ear
    5: 11,   # left_shoulder
    6: 12,   # right_shoulder
    7: 13,   # left_elbow
    8: 14,   # right_elbow
    9: 15,   # left_wrist
    10: 16,  # right_wrist
    11: 23,  # left_hip
    12: 24,  # right_hip
    13: 25,  # left_knee
    14: 26,  # right_knee
    15: 27,  # left_ankle
    16: 28,  # right_ankle
}

# Fighter bounding box colors (BGR for OpenCV)
FIGHTER_COLORS_BGR = {
    0: (255, 150, 50),   # Blue (fighter A)
    1: (50, 50, 255),    # Red (fighter B)
}
FIGHTER_COLORS_HEX = {
    0: "#3296FF",  # Blue
    1: "#FF3232",  # Red
}
FIGHTER_LABELS = {
    0: "Fighter A",
    1: "Fighter B",
}

# Load model lazily
_yolo_model = None


def _get_model():
    """Load YOLOv8-Pose model (cached)."""
    global _yolo_model
    if _yolo_model is None:
        _yolo_model = YOLO("yolov8m-pose.pt")
    return _yolo_model


def _coco_to_mediapipe_landmarks(coco_kpts):
    """Convert COCO 17 keypoints to MediaPipe-compatible 33-landmark array.

    Args:
        coco_kpts: Array of shape (17, 3) — x, y, confidence per keypoint.

    Returns:
        Array of shape (33, 4) — x, y, z, visibility per landmark.
        Missing landmarks are interpolated or set to zero visibility.
    """
    landmarks = np.zeros((33, 4), dtype=np.float32)

    for coco_idx, mp_idx in COCO_TO_MP.items():
        x, y, conf = coco_kpts[coco_idx]
        landmarks[mp_idx] = [x, y, 0.0, conf]

    # Interpolate missing landmarks from available ones
    # Mouth corners (MP 9, 10) from nose and ears
    if landmarks[0][3] > 0:  # nose available
        nose = landmarks[0][:2]
        left_ear = landmarks[7][:2] if landmarks[7][3] > 0 else nose
        right_ear = landmarks[8][:2] if landmarks[8][3] > 0 else nose
        mouth_left = (nose + left_ear) / 2
        mouth_left[1] += 0.02  # slightly below nose
        mouth_right = (nose + right_ear) / 2
        mouth_right[1] += 0.02
        landmarks[9] = [mouth_left[0], mouth_left[1], 0.0, 0.3]
        landmarks[10] = [mouth_right[0], mouth_right[1], 0.0, 0.3]

    # Inner/outer eyes (MP 1,3,4,6) from eyes and nose
    if landmarks[2][3] > 0:  # left_eye
        landmarks[1] = landmarks[2].copy()  # left_eye_inner ~ left_eye
        landmarks[1][3] = 0.3
        landmarks[3] = landmarks[2].copy()  # left_eye_outer ~ left_eye
        landmarks[3][3] = 0.3
    if landmarks[5][3] > 0:  # right_eye
        landmarks[4] = landmarks[5].copy()  # right_eye_inner ~ right_eye
        landmarks[4][3] = 0.3
        landmarks[6] = landmarks[5].copy()  # right_eye_outer ~ right_eye
        landmarks[6][3] = 0.3

    # Hand landmarks (MP 17-22: pinky, index, thumb for each hand)
    # Approximate from wrist position
    for wrist_mp, offsets in [(15, [17, 19, 21]), (16, [18, 20, 22])]:
        if landmarks[wrist_mp][3] > 0:
            for idx in offsets:
                landmarks[idx] = landmarks[wrist_mp].copy()
                landmarks[idx][3] = 0.2  # low visibility

    # Foot landmarks (MP 29-32: heel, foot_index for each foot)
    for ankle_mp, offsets in [(27, [29, 31]), (28, [30, 32])]:
        if landmarks[ankle_mp][3] > 0:
            for idx in offsets:
                landmarks[idx] = landmarks[ankle_mp].copy()
                landmarks[idx][3] = 0.2

    return landmarks


def _extract_thumbnail(frame, bbox, pad_ratio=0.15):
    """Crop a thumbnail of a fighter from a frame using their bounding box.

    Args:
        frame: Full video frame (BGR).
        bbox: (x1, y1, x2, y2) bounding box.
        pad_ratio: Padding ratio around the bbox.

    Returns:
        Base64-encoded JPEG thumbnail string.
    """
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = [int(v) for v in bbox]

    # Add padding
    bw, bh = x2 - x1, y2 - y1
    pad_x = int(bw * pad_ratio)
    pad_y = int(bh * pad_ratio)
    x1 = max(0, x1 - pad_x)
    y1 = max(0, y1 - pad_y)
    x2 = min(w, x2 + pad_x)
    y2 = min(h, y2 + pad_y)

    crop = frame[y1:y2, x1:x2]
    if crop.size == 0:
        return ""

    # Resize to reasonable thumbnail size
    thumb_h = 256
    aspect = crop.shape[1] / crop.shape[0]
    thumb_w = int(thumb_h * aspect)
    thumb = cv2.resize(crop, (thumb_w, thumb_h))

    _, buf = cv2.imencode(".jpg", thumb, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return base64.b64encode(buf).decode("utf-8")


def _generate_overview_frame(frame, fighter_bboxes):
    """Draw colored bounding boxes on a frame for all fighters.

    Args:
        frame: Full video frame (BGR).
        fighter_bboxes: dict {fighter_idx: (x1, y1, x2, y2)}

    Returns:
        Base64-encoded JPEG of the annotated frame.
    """
    annotated = frame.copy()

    for fighter_idx, bbox in fighter_bboxes.items():
        x1, y1, x2, y2 = [int(v) for v in bbox]
        color = FIGHTER_COLORS_BGR.get(fighter_idx, (255, 255, 255))
        label = FIGHTER_LABELS.get(fighter_idx, f"Fighter {fighter_idx}")

        # Draw box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 3)

        # Draw label background
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.8
        thickness = 2
        (tw, th), _ = cv2.getTextSize(label, font, font_scale, thickness)
        cv2.rectangle(annotated, (x1, y1 - th - 10), (x1 + tw + 6, y1), color, -1)
        cv2.putText(annotated, label, (x1 + 3, y1 - 5), font, font_scale,
                    (255, 255, 255), thickness)

    # Resize for reasonable file size
    max_w = 800
    if annotated.shape[1] > max_w:
        scale = max_w / annotated.shape[1]
        annotated = cv2.resize(annotated, None, fx=scale, fy=scale)

    _, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return base64.b64encode(buf).decode("utf-8")


def process_video(video_path, sample_fps=10):
    """Process a video to extract multi-person pose landmarks with tracking.

    Detects and tracks up to 2 fighters using YOLOv8-Pose + ByteTrack.

    Args:
        video_path: Path to the video file.
        sample_fps: Target frames per second to sample.

    Returns:
        dict with:
            - fighters: dict keyed by fighter index (0, 1) with:
                - landmarks: list of (frame_idx, landmarks_array) tuples
                - thumbnail_base64: cropped thumbnail of this fighter
                - color: hex color for UI
                - label: "Fighter A" or "Fighter B"
            - overview_frame_base64: full frame with colored bounding boxes
            - video_fps: original video FPS
            - total_frames: total frame count
    """
    model = _get_model()

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    if video_fps <= 0:
        video_fps = 30.0
    frame_interval = max(1, int(video_fps / sample_fps))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Collect per-track data
    # track_data[track_id] = list of (frame_idx, landmarks, bbox)
    track_data = {}
    frame_idx = 0
    overview_frame = None
    overview_bboxes = {}
    thumbnail_frame = None
    thumbnail_bboxes = {}

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_interval == 0:
            # Run YOLOv8-Pose with ByteTrack tracking
            results = model.track(
                frame,
                persist=True,
                tracker="bytetrack.yaml",
                verbose=False,
                conf=0.3,
            )

            if results and len(results) > 0:
                result = results[0]

                if result.boxes is not None and result.boxes.id is not None:
                    boxes = result.boxes
                    keypoints = result.keypoints

                    for i in range(len(boxes)):
                        track_id = int(boxes.id[i].item())
                        bbox = boxes.xyxy[i].cpu().numpy()  # (x1, y1, x2, y2)

                        # Get keypoints for this detection
                        if keypoints is not None and i < len(keypoints):
                            kpts = keypoints[i].data.cpu().numpy()[0]  # (17, 3)

                            # Normalize keypoints to 0-1 range relative to frame
                            h, w = frame.shape[:2]
                            kpts_norm = kpts.copy()
                            kpts_norm[:, 0] /= w
                            kpts_norm[:, 1] /= h

                            landmarks = _coco_to_mediapipe_landmarks(kpts_norm)

                            if track_id not in track_data:
                                track_data[track_id] = []
                            track_data[track_id].append((frame_idx, landmarks, bbox))

                            # Save first good frame for thumbnails
                            if thumbnail_frame is None and len(track_data) >= 1:
                                thumbnail_frame = frame.copy()

            # Save a frame around 15% into the video for overview
            if overview_frame is None and frame_idx > total_frames * 0.15:
                overview_frame = frame.copy()

        frame_idx += 1

    cap.release()

    if not track_data:
        return {
            "fighters": {},
            "overview_frame_base64": "",
            "video_fps": video_fps,
            "total_frames": total_frames,
        }

    # Identify the top 2 most-detected track IDs
    track_counts = {tid: len(data) for tid, data in track_data.items()}
    sorted_tracks = sorted(track_counts.keys(), key=lambda t: track_counts[t], reverse=True)
    top_tracks = sorted_tracks[:2]

    # Build fighter data
    fighters = {}
    fighter_bboxes_for_overview = {}

    for fighter_idx, track_id in enumerate(top_tracks):
        data = track_data[track_id]
        landmarks_list = [(fidx, lm) for fidx, lm, _ in data]
        bboxes = [(fidx, bb) for fidx, _, bb in data]

        # Get a representative bbox for thumbnail (from early in the video)
        early_idx = min(len(data) - 1, max(0, len(data) // 5))
        rep_bbox = data[early_idx][2]

        # Extract thumbnail
        thumb_frame = thumbnail_frame if thumbnail_frame is not None else (
            overview_frame if overview_frame is not None else None
        )
        thumbnail_b64 = ""
        if thumb_frame is not None:
            thumbnail_b64 = _extract_thumbnail(thumb_frame, rep_bbox)

        fighter_bboxes_for_overview[fighter_idx] = rep_bbox

        fighters[str(fighter_idx)] = {
            "landmarks": landmarks_list,
            "thumbnail_base64": thumbnail_b64,
            "color": FIGHTER_COLORS_HEX.get(fighter_idx, "#FFFFFF"),
            "label": FIGHTER_LABELS.get(fighter_idx, f"Fighter {fighter_idx}"),
            "track_id": track_id,
            "frame_count": len(landmarks_list),
        }

    # Generate overview frame with bounding boxes
    overview_b64 = ""
    ov_frame = overview_frame if overview_frame is not None else thumbnail_frame
    if ov_frame is not None and fighter_bboxes_for_overview:
        overview_b64 = _generate_overview_frame(ov_frame, fighter_bboxes_for_overview)

    return {
        "fighters": fighters,
        "overview_frame_base64": overview_b64,
        "video_fps": video_fps,
        "total_frames": total_frames,
    }
