# from flask import Flask, request, jsonify
# import tensorflow as tf
# import cv2
# import numpy as np
# import firebase_admin
# from firebase_admin import credentials, firestore
# import firebase_admin
# from firebase_admin import credentials, firestore

# # Load the Firebase credentials
# cred = credentials.Certificate("serviceAccountKey.json")
# firebase_admin.initialize_app(cred)

# # Initialize Firestore database
# db = firestore.client()


# app = Flask(__name__)

# # Initialize Firebase
# cred = credentials.Certificate("path/to/serviceAccountKey.json")  # Replace with your actual path
# firebase_admin.initialize_app(cred)
# db = firestore.client()

# @app.route('/analyze', methods=['POST'])
# def analyze():
#     video_file = request.files['video']
    
#     # TODO: Process video using TensorFlow & OpenPose (future implementation)
#     analysis_results = {"message": "Video received for AI processing"}

#     return jsonify(analysis_results)

# if __name__ == '__main__':
#     app.run(debug=True, port=5000)

from flask import Flask, request, jsonify
import tensorflow as tf
import cv2
import numpy as np
import firebase_admin
from firebase_admin import credentials, firestore, storage
import os

app = Flask(__name__)

# Load Firebase Credentials
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {"storageBucket": "your-project-id.appspot.com"})  # Replace with your actual Firebase storage bucket

# Initialise Firestore Database
db = firestore.client()
bucket = storage.bucket()

# Upload Video Route
@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video file uploaded"}), 400

    video_file = request.files['video']
    filename = video_file.filename
    file_path = os.path.join("uploads", filename)
    
    # Save video temporarily
    os.makedirs("uploads", exist_ok=True)
    video_file.save(file_path)
    
    # Upload video to Firebase Storage
    blob = bucket.blob(f"videos/{filename}")
    blob.upload_from_filename(file_path)
    blob.make_public()
    video_url = blob.public_url

    # Save metadata to Firestore
    video_doc = db.collection("videos").document()
    video_doc.set({
        "filename": filename,
        "video_url": video_url
    })

    # Remove temporary file
    os.remove(file_path)

    return jsonify({"message": "Video uploaded successfully!", "video_url": video_url})

# ✅ AI Analysis Route (Pose Detection)
@app.route('/analyze', methods=['POST'])
def analyze_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video file uploaded"}), 400

    video_file = request.files['video']
    filename = video_file.filename
    file_path = os.path.join("uploads", filename)

    # Save video temporarily
    os.makedirs("uploads", exist_ok=True)
    video_file.save(file_path)

    # 🔥 Process Video with AI (TODO: OpenPose Integration)
    analysis_results = process_video(file_path)

    # Save AI results to Firestore
    analysis_doc = db.collection("analysis").document()
    analysis_doc.set({
        "filename": filename,
        "results": analysis_results
    })

    # Remove temporary file
    os.remove(file_path)

    return jsonify({"message": "Video analyzed successfully!", "results": analysis_results})

# ✅ AI Processing Function (Placeholder)
def process_video(video_path):
    # TODO: Integrate OpenPose and TensorFlow AI model for analysis
    return {"footwork": "Good", "defense": "Needs improvement", "punch_accuracy": "85%"}

# ✅ Test Route
@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "StrikeStream Backend is Running!"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
