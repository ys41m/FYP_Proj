"""
Strike Stream API — Boxing video analysis with multi-person tracking.

Endpoints:
    POST /analyze              Upload & analyze a boxing video (returns session + fighter previews)
    GET  /analysis/<sid>/fighter/<fid>  Get full analysis for a specific fighter
    GET  /analysis/<sid>/summary       Get session summary (scores + thumbnails for both fighters)
    GET  /presets               List all fighter style presets
    GET  /presets/<key>         Get specific fighter preset details
    POST /train                Trigger model training
"""

from flask import Flask, request, jsonify
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS
import os
import uuid
import numpy as np


class NumpyJSONProvider(DefaultJSONProvider):
    """JSON provider that handles numpy types transparently."""

    @staticmethod
    def default(o):
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        return DefaultJSONProvider.default(o)


app = Flask(__name__)
app.json_provider_class = NumpyJSONProvider
app.json = NumpyJSONProvider(app)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_VIDEO_DURATION_SECONDS = 120  # 2 minutes

# Lazy-load heavy ML modules to speed up startup
_model = None


def _get_model():
    global _model
    if _model is None:
        from move_classifier import load_model
        _model = load_model()  # Returns None if no trained model yet
    return _model


# -------------------------------------------------------------------
# Health check
# -------------------------------------------------------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Strike Stream API is running", "version": "2.0.0"})


# -------------------------------------------------------------------
# Main analysis endpoint
# -------------------------------------------------------------------

def _download_video_from_url(url):
    """Download a video from a URL (YouTube, direct link, etc.) using yt-dlp.

    Returns the path to the downloaded file.
    Raises ValueError on failure.
    """
    import yt_dlp
    import glob as globmod

    temp_filename = f"{uuid.uuid4().hex}"
    temp_path = os.path.join(UPLOAD_DIR, temp_filename + ".mp4")

    ydl_opts = {
        # Prefer a single combined mp4 stream to avoid needing ffmpeg for merging.
        "format": "best[height<=720][ext=mp4]/best[ext=mp4]/best[height<=720]/best",
        "outtmpl": os.path.join(UPLOAD_DIR, temp_filename + ".%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 30,
        # Use browser cookies to bypass YouTube 403 bot detection.
        # Tries Chrome first, then Edge, then Firefox.
        "cookiesfrombrowser": ("chrome",),
        "extractor_args": {"youtube": {"player_client": ["ios", "web"]}},
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        },
    }

    # Try multiple cookie sources — YouTube blocks requests without valid cookies
    browser_attempts = [("chrome",), ("edge",), ("firefox",), None]
    last_error = None

    for browser_cookies in browser_attempts:
        # Clean up any partial downloads from prior attempt
        for f in globmod.glob(os.path.join(UPLOAD_DIR, temp_filename + ".*")):
            os.remove(f)

        opts = dict(ydl_opts)
        if browser_cookies is not None:
            opts["cookiesfrombrowser"] = browser_cookies
        else:
            opts.pop("cookiesfrombrowser", None)

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.extract_info(url, download=True)

                # Find the downloaded file (extension may vary)
                pattern = os.path.join(UPLOAD_DIR, temp_filename + ".*")
                matches = globmod.glob(pattern)
                if not matches:
                    raise ValueError("Download completed but output file not found.")

                downloaded = matches[0]
                if downloaded != temp_path:
                    os.rename(downloaded, temp_path)

                return temp_path
        except Exception as e:
            last_error = e
            continue

    # All attempts failed — clean up and raise
    for f in globmod.glob(os.path.join(UPLOAD_DIR, temp_filename + ".*")):
        os.remove(f)
    raise ValueError(f"Could not download video: {str(last_error)}")


@app.route("/analyze", methods=["POST"])
def analyze_video():
    """Upload and analyze a boxing video with multi-person tracking.

    Accepts either:
      - A file upload via multipart form (field name: 'video')
      - A JSON body with {"url": "https://..."} for YouTube / direct video links

    Returns:
        {
            session_id: str,
            fighters: [{ id, thumbnail_base64, color, label, overall_score }],
            overview_frame_base64: str,
            duration_seconds: float,
            fighter_count: int,
        }
    """
    temp_path = None
    url_download = False

    try:
        # Check if this is a URL-based request
        if request.is_json or (request.content_type and "json" in request.content_type):
            data = request.get_json(silent=True) or {}
            url = data.get("url", "").strip()
            if not url:
                return jsonify({"error": "No URL provided. Send a JSON body with a 'url' field."}), 400
            temp_path = _download_video_from_url(url)
            url_download = True

        elif "video" in request.files:
            video_file = request.files["video"]
            if not video_file.filename:
                return jsonify({"error": "Empty filename"}), 400

            ext = os.path.splitext(video_file.filename)[1] or ".mp4"
            temp_filename = f"{uuid.uuid4().hex}{ext}"
            temp_path = os.path.join(UPLOAD_DIR, temp_filename)
            video_file.save(temp_path)

        else:
            # Check if URL was sent as form field
            url = request.form.get("url", "").strip()
            if url:
                temp_path = _download_video_from_url(url)
                url_download = True
            else:
                return jsonify({"error": "No video file or URL provided."}), 400

        # Validate duration
        import cv2
        cap = cv2.VideoCapture(temp_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = frame_count / fps
        cap.release()

        if duration > MAX_VIDEO_DURATION_SECONDS:
            return jsonify({
                "error": f"Video too long ({duration:.1f}s). Maximum is {MAX_VIDEO_DURATION_SECONDS}s (2 minutes)."
            }), 400

        # Multi-person pose extraction with tracking
        from multi_pose_estimator import process_video
        pose_result = process_video(temp_path, sample_fps=10)

        fighters_data = pose_result.get("fighters", {})
        video_fps = pose_result.get("video_fps", 30.0)

        if not fighters_data:
            return jsonify({
                "error": "No human poses detected in the video. Ensure at least one person is visible."
            }), 422

        # Classify moves and run analysis for each fighter
        from move_classifier import predict_moves
        from boxing_analyzer import analyze_sequence, analyze_both_fighters
        from analysis_session import session_store

        model = _get_model()

        fighter_ids = sorted(fighters_data.keys())

        if len(fighter_ids) == 1:
            # Solo video — analyze the single fighter
            fdata = fighters_data[fighter_ids[0]]
            landmarks = fdata["landmarks"]
            preds = predict_moves(landmarks, model=model)
            analysis = analyze_sequence(landmarks, preds, video_fps)

            # Create session with single fighter
            session_id = session_store.create_session(
                duration_seconds=round(duration, 1),
                video_fps=video_fps,
                overview_frame_base64=pose_result.get("overview_frame_base64", ""),
            )
            session_store.add_fighter(
                session_id, fighter_ids[0], analysis,
                thumbnail_base64=fdata.get("thumbnail_base64", ""),
                color=fdata.get("color", "#3296FF"),
                label=fdata.get("label", "Fighter A"),
            )

        else:
            # Two fighters — analyze both with cross-referencing
            f0 = fighters_data[fighter_ids[0]]
            f1 = fighters_data[fighter_ids[1]]

            preds_0 = predict_moves(f0["landmarks"], model=model)
            preds_1 = predict_moves(f1["landmarks"], model=model)

            both = analyze_both_fighters(
                f0["landmarks"], f1["landmarks"],
                preds_0, preds_1, video_fps
            )

            session_id = session_store.create_session(
                duration_seconds=round(duration, 1),
                video_fps=video_fps,
                overview_frame_base64=pose_result.get("overview_frame_base64", ""),
            )

            session_store.add_fighter(
                session_id, fighter_ids[0], both["fighter_a"],
                thumbnail_base64=f0.get("thumbnail_base64", ""),
                color=f0.get("color", "#3296FF"),
                label=f0.get("label", "Fighter A"),
            )
            session_store.add_fighter(
                session_id, fighter_ids[1], both["fighter_b"],
                thumbnail_base64=f1.get("thumbnail_base64", ""),
                color=f1.get("color", "#FF3232"),
                label=f1.get("label", "Fighter B"),
            )

        # Build response with fighter previews
        summary = session_store.get_session_summary(session_id)

        return jsonify({
            "success": True,
            "session_id": session_id,
            "fighters": summary["fighters"],
            "overview_frame_base64": summary["overview_frame_base64"],
            "duration_seconds": round(duration, 1),
            "fighter_count": len(fighter_ids),
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


# -------------------------------------------------------------------
# Session-based result endpoints
# -------------------------------------------------------------------

@app.route("/analysis/<session_id>/fighter/<fighter_id>", methods=["GET"])
def get_fighter_analysis(session_id, fighter_id):
    """Get the full personalized analysis for a specific fighter in a session.

    Returns the complete analysis dict including opponent-aware coaching
    (if two fighters were detected).
    """
    from analysis_session import session_store

    analysis = session_store.get_fighter_analysis(session_id, fighter_id)
    if analysis is None:
        return jsonify({"error": "Session or fighter not found."}), 404

    session = session_store.get_session(session_id)
    return jsonify({
        "success": True,
        "session_id": session_id,
        "fighter_id": fighter_id,
        "duration_seconds": session.duration_seconds if session else 0,
        "analysis": analysis,
    })


@app.route("/analysis/<session_id>/summary", methods=["GET"])
def get_session_summary(session_id):
    """Get a summary of a session — scores, thumbnails, and overview for
    the fighter selection screen.
    """
    from analysis_session import session_store

    summary = session_store.get_session_summary(session_id)
    if summary is None:
        return jsonify({"error": "Session not found."}), 404

    return jsonify({
        "success": True,
        **summary,
    })


# -------------------------------------------------------------------
# Presets
# -------------------------------------------------------------------

@app.route("/presets", methods=["GET"])
def get_presets():
    """Return all available fighter style presets."""
    from fighter_presets import get_preset_summary_list
    return jsonify({"presets": get_preset_summary_list()})


@app.route("/presets/<fighter_key>", methods=["GET"])
def get_preset_detail(fighter_key):
    """Return detailed info for a specific fighter preset."""
    from fighter_presets import get_preset
    preset = get_preset(fighter_key)
    if not preset:
        return jsonify({"error": f"Unknown fighter: {fighter_key}"}), 404
    return jsonify({"preset": preset})


# -------------------------------------------------------------------
# Training
# -------------------------------------------------------------------

@app.route("/train", methods=["POST"])
def trigger_training():
    """Trigger model training. Body can include {"synthetic": true} to use synthetic data."""
    data = request.get_json(silent=True) or {}
    use_synthetic = data.get("synthetic", True)
    epochs = data.get("epochs", 50)

    from train_model import train
    try:
        model, history = train(use_synthetic=use_synthetic, epochs=epochs)
        global _model
        _model = model
        return jsonify({
            "success": True,
            "message": "Model trained successfully",
            "final_accuracy": float(history.history["val_accuracy"][-1]),
        })
    except Exception as e:
        return jsonify({"error": f"Training failed: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
