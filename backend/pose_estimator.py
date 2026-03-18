"""
Pose estimation utilities.

Provides shared functions for computing boxing angles, stance detection,
and frame features. These are used by both the legacy MediaPipe pipeline
and the new YOLOv8-Pose multi-person pipeline.
"""

import numpy as np


LANDMARK_NAMES = [
    "nose", "left_eye_inner", "left_eye", "left_eye_outer",
    "right_eye_inner", "right_eye", "right_eye_outer",
    "left_ear", "right_ear", "mouth_left", "mouth_right",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_pinky", "right_pinky",
    "left_index", "right_index", "left_thumb", "right_thumb",
    "left_hip", "right_hip", "left_knee", "right_knee",
    "left_ankle", "right_ankle", "left_heel", "right_heel",
    "left_foot_index", "right_foot_index"
]

# Key landmark indices for boxing analysis
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28
NOSE = 0


def calculate_angle(a, b, c):
    """Calculate angle at point b given three points a, b, c."""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    ba = a - b
    bc = c - b
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    angle = np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))
    return angle



def compute_boxing_angles(landmarks):
    """Compute key boxing-relevant joint angles from a single frame's landmarks.

    Returns dict with angle measurements.
    """
    def pt(idx):
        return landmarks[idx][:3]

    angles = {}

    # Elbow angles (arm extension — low = tucked, high = extended)
    angles["left_elbow"] = calculate_angle(pt(LEFT_SHOULDER), pt(LEFT_ELBOW), pt(LEFT_WRIST))
    angles["right_elbow"] = calculate_angle(pt(RIGHT_SHOULDER), pt(RIGHT_ELBOW), pt(RIGHT_WRIST))

    # Shoulder angles (arm raise)
    angles["left_shoulder"] = calculate_angle(pt(LEFT_HIP), pt(LEFT_SHOULDER), pt(LEFT_ELBOW))
    angles["right_shoulder"] = calculate_angle(pt(RIGHT_HIP), pt(RIGHT_SHOULDER), pt(RIGHT_ELBOW))

    # Knee angles (bend/crouch)
    angles["left_knee"] = calculate_angle(pt(LEFT_HIP), pt(LEFT_KNEE), pt(LEFT_ANKLE))
    angles["right_knee"] = calculate_angle(pt(RIGHT_HIP), pt(RIGHT_KNEE), pt(RIGHT_ANKLE))

    # Hip angles (torso rotation proxy)
    angles["left_hip"] = calculate_angle(pt(LEFT_SHOULDER), pt(LEFT_HIP), pt(LEFT_KNEE))
    angles["right_hip"] = calculate_angle(pt(RIGHT_SHOULDER), pt(RIGHT_HIP), pt(RIGHT_KNEE))

    # Guard height: wrist Y relative to nose Y (lower = higher guard)
    nose_y = landmarks[NOSE][1]
    angles["left_guard_height"] = landmarks[LEFT_WRIST][1] - nose_y
    angles["right_guard_height"] = landmarks[RIGHT_WRIST][1] - nose_y

    return angles


def detect_stance(landmarks):
    """Detect orthodox vs southpaw stance based on foot and shoulder positioning.

    Returns 'orthodox', 'southpaw', or 'square'.
    """
    left_foot_x = landmarks[LEFT_ANKLE][0]
    right_foot_x = landmarks[RIGHT_ANKLE][0]
    left_shoulder_x = landmarks[LEFT_SHOULDER][0]
    right_shoulder_x = landmarks[RIGHT_SHOULDER][0]

    # In MediaPipe, X increases left-to-right in the image.
    # Orthodox: left foot/shoulder forward (closer to opponent, lower X if facing right)
    # We use the relative positioning of feet.
    foot_diff = left_foot_x - right_foot_x
    shoulder_diff = left_shoulder_x - right_shoulder_x

    threshold = 0.03  # Normalized coordinate threshold

    if foot_diff < -threshold:
        return "orthodox"
    elif foot_diff > threshold:
        return "southpaw"
    else:
        return "square"


def compute_frame_features(landmarks):
    """Compute a feature vector from a single frame's landmarks for classification.

    Returns a 1D numpy array combining:
    - Flattened normalized landmarks (33 * 3 = 99 values, xyz only)
    - Key boxing angles (10 values)
    Total: 109 features per frame
    """
    # Normalize landmarks relative to hip center
    hip_center = (landmarks[LEFT_HIP][:3] + landmarks[RIGHT_HIP][:3]) / 2.0
    normalized = landmarks[:, :3] - hip_center
    flat_landmarks = normalized.flatten()  # 99 values

    angles = compute_boxing_angles(landmarks)
    angle_values = np.array([
        angles["left_elbow"], angles["right_elbow"],
        angles["left_shoulder"], angles["right_shoulder"],
        angles["left_knee"], angles["right_knee"],
        angles["left_hip"], angles["right_hip"],
        angles["left_guard_height"], angles["right_guard_height"]
    ], dtype=np.float32)

    # Normalize angles to 0-1 range (angles are 0-180, guard heights are roughly -0.5 to 0.5)
    angle_values[:8] = angle_values[:8] / 180.0
    angle_values[8:] = (angle_values[8:] + 0.5)  # Shift guard heights to positive range

    return np.concatenate([flat_landmarks, angle_values])
