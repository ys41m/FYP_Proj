"""
Boxing move classifier using an LSTM model trained on pose landmark sequences.
Classifies sequences of frames into boxing moves: jabs, crosses, hooks, uppercuts,
slips, bobs, blocks, etc.
"""

import numpy as np
import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
import tensorflow as tf
from tensorflow import keras

from pose_estimator import compute_frame_features

# Model parameters
SEQUENCE_LENGTH = 15   # Number of frames per classification window
FEATURE_DIM = 109      # Features per frame (99 landmarks + 10 angles)
NUM_CLASSES = 12        # Number of move classes

MOVE_LABELS = [
    "jab",
    "cross",
    "lead_hook",
    "rear_hook",
    "lead_uppercut",
    "rear_uppercut",
    "slip_left",
    "slip_right",
    "bob_and_weave",
    "block",
    "idle_guard",
    "footwork"
]

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "move_classifier.keras")


def build_model():
    """Build the LSTM-based move classification model."""
    model = keras.Sequential([
        keras.layers.Input(shape=(SEQUENCE_LENGTH, FEATURE_DIM)),

        # Batch normalization on input
        keras.layers.BatchNormalization(),

        # Bidirectional LSTM layers
        keras.layers.Bidirectional(
            keras.layers.LSTM(128, return_sequences=True, dropout=0.3)
        ),
        keras.layers.Bidirectional(
            keras.layers.LSTM(64, return_sequences=False, dropout=0.3)
        ),

        # Dense classification head
        keras.layers.Dense(64, activation="relu"),
        keras.layers.Dropout(0.4),
        keras.layers.Dense(32, activation="relu"),
        keras.layers.Dropout(0.3),
        keras.layers.Dense(NUM_CLASSES, activation="softmax"),
    ])

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )

    return model


def load_model():
    """Load the trained model from disk. Returns None if no trained model exists."""
    if os.path.exists(MODEL_PATH):
        return keras.models.load_model(MODEL_PATH)
    return None


def predict_moves(all_landmarks, model=None):
    """Classify boxing moves from a sequence of landmarks.

    Args:
        all_landmarks: List of (frame_idx, landmarks_array) tuples.
        model: Optional pre-loaded keras model. If None, loads from disk.

    Returns:
        List of predicted move labels, one per sliding window.
    """
    if model is None:
        model = load_model()

    # If no trained model exists, use heuristic classification
    if model is None:
        return _heuristic_classify(all_landmarks)

    # Compute features for each frame
    features = []
    for _, landmarks in all_landmarks:
        feat = compute_frame_features(landmarks)
        features.append(feat)
    features = np.array(features)

    # Create sliding windows
    predictions = []
    stride = SEQUENCE_LENGTH // 2  # 50% overlap

    for start in range(0, len(features) - SEQUENCE_LENGTH + 1, stride):
        window = features[start:start + SEQUENCE_LENGTH]
        window = np.expand_dims(window, axis=0)  # (1, seq_len, features)
        pred = model.predict(window, verbose=0)
        label_idx = np.argmax(pred[0])
        confidence = float(pred[0][label_idx])
        if confidence > 0.4:
            predictions.append(MOVE_LABELS[label_idx])
        else:
            predictions.append("idle_guard")

    return predictions


def _heuristic_classify(all_landmarks):
    """Rule-based move classification when no trained model is available.

    Uses joint angles and positional changes to detect basic moves.
    """
    predictions = []

    for i in range(len(all_landmarks)):
        _, landmarks = all_landmarks[i]

        from pose_estimator import compute_boxing_angles, LEFT_WRIST, RIGHT_WRIST, NOSE

        angles = compute_boxing_angles(landmarks)

        # Detect punches by arm extension
        left_extended = angles["left_elbow"] > 140
        right_extended = angles["right_elbow"] > 140
        left_raised = angles["left_shoulder"] > 60
        right_raised = angles["right_shoulder"] > 60

        # Wrist height relative to nose
        left_wrist_y = landmarks[LEFT_WRIST][1]
        right_wrist_y = landmarks[RIGHT_WRIST][1]
        nose_y = landmarks[NOSE][1]

        # In MediaPipe, lower Y = higher in frame
        left_high = left_wrist_y < nose_y
        right_high = right_wrist_y < nose_y

        # Head position change for slips
        if i > 0:
            prev_landmarks = all_landmarks[i - 1][1]
            head_dx = landmarks[NOSE][0] - prev_landmarks[NOSE][0]
            head_dy = landmarks[NOSE][1] - prev_landmarks[NOSE][1]
        else:
            head_dx = 0
            head_dy = 0

        # Classification logic
        move = "idle_guard"

        if left_extended and left_raised and left_high:
            if angles["left_shoulder"] > 80:
                move = "jab"
            else:
                move = "lead_hook"
        elif right_extended and right_raised and right_high:
            if angles["right_shoulder"] > 80:
                move = "cross"
            else:
                move = "rear_hook"
        elif left_raised and not left_extended and landmarks[LEFT_WRIST][1] < landmarks[LEFT_ELBOW][1]:
            move = "lead_uppercut"
        elif right_raised and not right_extended and landmarks[RIGHT_WRIST][1] < landmarks[RIGHT_ELBOW][1]:
            move = "rear_uppercut"
        elif abs(head_dx) > 0.03:
            move = "slip_left" if head_dx < 0 else "slip_right"
        elif head_dy > 0.03:
            move = "bob_and_weave"
        elif left_high and right_high and not left_extended and not right_extended:
            move = "block"

        predictions.append(move)

    return predictions
