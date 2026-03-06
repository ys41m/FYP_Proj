from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid

app = Flask(__name__)
CORS(app)

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


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "BoxAnalytics API is running", "version": "1.0.0"})


@app.route("/analyze", methods=["POST"])
def analyze_video():
    """Upload and analyze a boxing video.

    Accepts a video file (up to 2 minutes), runs pose estimation,
    move classification, and returns a full boxing analysis.
    """
    if "video" not in request.files:
        return jsonify({"error": "No video file provided. Send a 'video' field."}), 400

    video_file = request.files["video"]
    if not video_file.filename:
        return jsonify({"error": "Empty filename"}), 400

    # Save temporarily
    ext = os.path.splitext(video_file.filename)[1] or ".mp4"
    temp_filename = f"{uuid.uuid4().hex}{ext}"
    temp_path = os.path.join(UPLOAD_DIR, temp_filename)

    try:
        video_file.save(temp_path)

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

        # Extract pose landmarks
        from pose_estimator import extract_landmarks_from_video
        all_landmarks = extract_landmarks_from_video(temp_path, sample_fps=10)

        if not all_landmarks:
            return jsonify({
                "error": "No human poses detected in the video. Ensure the person is visible."
            }), 422

        # Classify moves
        from move_classifier import predict_moves
        model = _get_model()
        move_predictions = predict_moves(all_landmarks, model=model)

        # Run full analysis
        from boxing_analyzer import analyze_sequence
        results = analyze_sequence(all_landmarks, move_predictions)

        return jsonify({
            "success": True,
            "duration_seconds": round(duration, 1),
            "analysis": results,
        })

    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


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
