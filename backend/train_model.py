"""
Training pipeline for the boxing move classification model.

Usage:
    python train_model.py --data_dir ./training_data --epochs 50

Data directory structure:
    training_data/
        jab/
            video1.mp4
            video2.mp4
        cross/
            video1.mp4
        lead_hook/
            ...
        (one folder per move label)

The pipeline:
1. Reads videos from labeled folders
2. Extracts MediaPipe pose landmarks per frame
3. Computes feature vectors (landmarks + angles)
4. Creates sliding window sequences
5. Trains a bidirectional LSTM classifier
6. Saves the trained model

For initial training without real data, use --generate_synthetic to create
synthetic training data from heuristic pose patterns.
"""

import os
import sys
import argparse
import numpy as np
from pathlib import Path

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
import tensorflow as tf
from tensorflow import keras

from move_classifier import (
    build_model, MOVE_LABELS, SEQUENCE_LENGTH, FEATURE_DIM, NUM_CLASSES, MODEL_PATH
)
from pose_estimator import extract_landmarks_from_video, compute_frame_features


def load_training_data(data_dir):
    """Load and process training videos from labeled directories.

    Returns:
        X: array of shape (num_samples, SEQUENCE_LENGTH, FEATURE_DIM)
        y: array of shape (num_samples, NUM_CLASSES) one-hot encoded
    """
    X_sequences = []
    y_labels = []

    for label_idx, label in enumerate(MOVE_LABELS):
        label_dir = os.path.join(data_dir, label)
        if not os.path.isdir(label_dir):
            print(f"  Warning: No directory for label '{label}' at {label_dir}")
            continue

        video_files = [
            f for f in os.listdir(label_dir)
            if f.endswith(('.mp4', '.avi', '.mov', '.mkv'))
        ]

        print(f"  Processing {len(video_files)} videos for '{label}'...")

        for vf in video_files:
            video_path = os.path.join(label_dir, vf)
            try:
                all_landmarks = extract_landmarks_from_video(video_path, sample_fps=15)
            except Exception as e:
                print(f"    Error processing {vf}: {e}")
                continue

            if len(all_landmarks) < SEQUENCE_LENGTH:
                continue

            # Compute features
            features = []
            for _, landmarks in all_landmarks:
                feat = compute_frame_features(landmarks)
                features.append(feat)
            features = np.array(features)

            # Create sliding window sequences
            stride = max(1, SEQUENCE_LENGTH // 3)
            for start in range(0, len(features) - SEQUENCE_LENGTH + 1, stride):
                window = features[start:start + SEQUENCE_LENGTH]
                X_sequences.append(window)
                y_labels.append(label_idx)

    if not X_sequences:
        return None, None

    X = np.array(X_sequences, dtype=np.float32)
    y = keras.utils.to_categorical(y_labels, num_classes=NUM_CLASSES)

    return X, y


def generate_synthetic_data(num_samples_per_class=200):
    """Generate synthetic training data based on characteristic pose patterns.

    This creates rough approximations of boxing moves using known biomechanical
    properties. Not as good as real data but useful for bootstrapping.
    """
    print("Generating synthetic training data...")
    X_all = []
    y_all = []

    np.random.seed(42)

    for label_idx, label in enumerate(MOVE_LABELS):
        for _ in range(num_samples_per_class):
            sequence = _generate_synthetic_sequence(label)
            X_all.append(sequence)
            y_all.append(label_idx)

    X = np.array(X_all, dtype=np.float32)
    y = keras.utils.to_categorical(y_all, num_classes=NUM_CLASSES)

    # Shuffle
    indices = np.random.permutation(len(X))
    return X[indices], y[indices]


def _generate_synthetic_sequence(label):
    """Generate a single synthetic sequence for a given move label.

    Creates SEQUENCE_LENGTH frames of FEATURE_DIM features each,
    simulating the characteristic joint patterns of each move.
    """
    seq = np.zeros((SEQUENCE_LENGTH, FEATURE_DIM), dtype=np.float32)

    for t in range(SEQUENCE_LENGTH):
        progress = t / (SEQUENCE_LENGTH - 1)  # 0 to 1
        noise = np.random.normal(0, 0.02, FEATURE_DIM).astype(np.float32)

        # Base pose: normalized landmark positions (99 values) + angles (10 values)
        frame = np.random.normal(0, 0.05, FEATURE_DIM).astype(np.float32)

        # Angles are in indices 99-108
        # [left_elbow, right_elbow, left_shoulder, right_shoulder,
        #  left_knee, right_knee, left_hip, right_hip,
        #  left_guard_height, right_guard_height]

        if label == "jab":
            # Left arm extends forward, right stays guard
            frame[99] = (0.3 + 0.5 * progress) / 1.0   # left elbow extends
            frame[100] = 0.4                              # right stays bent
            frame[101] = (0.4 + 0.3 * progress) / 1.0   # left shoulder raises
            frame[102] = 0.3                              # right shoulder stays
            frame[107] = 0.5                              # right guard stays up
            frame[108] = 0.5 - 0.3 * progress            # left guard drops as punching

        elif label == "cross":
            frame[99] = 0.4
            frame[100] = (0.3 + 0.5 * progress) / 1.0   # right arm extends
            frame[101] = 0.3
            frame[102] = (0.4 + 0.3 * progress) / 1.0   # right shoulder raises
            frame[107] = 0.5 - 0.3 * progress
            frame[108] = 0.5

        elif label == "lead_hook":
            frame[99] = 0.5                               # elbow stays bent ~90
            frame[100] = 0.4
            frame[101] = (0.5 + 0.3 * progress) / 1.0   # shoulder raises significantly
            frame[102] = 0.3
            # Lateral wrist movement (in normalized landmarks)
            frame[15 * 3] = 0.1 * progress               # left wrist x moves

        elif label == "rear_hook":
            frame[99] = 0.4
            frame[100] = 0.5
            frame[101] = 0.3
            frame[102] = (0.5 + 0.3 * progress) / 1.0

        elif label == "lead_uppercut":
            frame[99] = (0.5 - 0.2 * progress)           # arm bends more
            frame[101] = (0.3 + 0.4 * progress) / 1.0   # shoulder drives up
            frame[108] = 0.5 - 0.4 * progress            # hand goes high

        elif label == "rear_uppercut":
            frame[100] = (0.5 - 0.2 * progress)
            frame[102] = (0.3 + 0.4 * progress) / 1.0
            frame[107] = 0.5 - 0.4 * progress

        elif label == "slip_left":
            # Head moves left and slightly down
            frame[0] = -0.05 * progress                   # nose x moves left
            frame[1] = 0.02 * progress                    # nose y moves down slightly
            frame[103] = 0.55 + 0.1 * progress            # knees bend slightly

        elif label == "slip_right":
            frame[0] = 0.05 * progress
            frame[1] = 0.02 * progress
            frame[103] = 0.55 + 0.1 * progress

        elif label == "bob_and_weave":
            # Significant knee bend and head drop
            phase = np.sin(progress * np.pi)
            frame[1] = 0.05 * phase                       # head drops then comes up
            frame[103] = 0.5 + 0.2 * phase                # knees bend
            frame[104] = 0.5 + 0.2 * phase
            frame[0] = 0.03 * np.sin(progress * 2 * np.pi)  # lateral head movement

        elif label == "block":
            # Both arms up, elbows tucked
            frame[99] = 0.35                               # arms bent tight
            frame[100] = 0.35
            frame[107] = 0.6                               # hands up high
            frame[108] = 0.6

        elif label == "idle_guard":
            frame[99] = 0.4
            frame[100] = 0.4
            frame[107] = 0.5
            frame[108] = 0.5
            frame[103] = 0.5
            frame[104] = 0.5

        elif label == "footwork":
            # Foot positions change
            ankle_indices = [27 * 3, 27 * 3 + 1, 28 * 3, 28 * 3 + 1]
            for idx in ankle_indices:
                if idx < 99:
                    frame[idx] = 0.03 * np.sin(progress * 2 * np.pi + np.random.random())

        frame += noise
        seq[t] = frame

    return seq


def train(data_dir=None, epochs=50, batch_size=32, use_synthetic=False):
    """Main training function."""
    print("=" * 60)
    print("Boxing Move Classifier Training Pipeline")
    print("=" * 60)

    if use_synthetic or data_dir is None:
        X_train, y_train = generate_synthetic_data(num_samples_per_class=300)
    else:
        print(f"\nLoading training data from: {data_dir}")
        X_train, y_train = load_training_data(data_dir)

    if X_train is None or len(X_train) == 0:
        print("ERROR: No training data available.")
        if data_dir:
            print(f"Ensure {data_dir} has subdirectories for each move label with video files.")
            print(f"Expected labels: {MOVE_LABELS}")
        return

    print(f"\nTraining data shape: X={X_train.shape}, y={y_train.shape}")

    # Split into train/validation
    split = int(0.85 * len(X_train))
    X_val = X_train[split:]
    y_val = y_train[split:]
    X_train = X_train[:split]
    y_train = y_train[:split]

    print(f"Train samples: {len(X_train)}, Validation samples: {len(X_val)}")

    # Build model
    model = build_model()
    model.summary()

    # Callbacks
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

    callbacks = [
        keras.callbacks.ModelCheckpoint(
            MODEL_PATH, monitor="val_accuracy", save_best_only=True, verbose=1
        ),
        keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=10, restore_best_weights=True
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=5, min_lr=1e-6
        ),
    ]

    # Train
    print(f"\nTraining for up to {epochs} epochs...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=callbacks,
        verbose=1
    )

    # Final evaluation
    val_loss, val_acc = model.evaluate(X_val, y_val, verbose=0)
    print(f"\nFinal validation accuracy: {val_acc:.4f}")
    print(f"Final validation loss: {val_loss:.4f}")
    print(f"\nModel saved to: {MODEL_PATH}")

    return model, history


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train boxing move classifier")
    parser.add_argument("--data_dir", type=str, default=None, help="Path to training data directory")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument(
        "--generate_synthetic", action="store_true",
        help="Generate and use synthetic training data"
    )
    args = parser.parse_args()

    train(
        data_dir=args.data_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        use_synthetic=args.generate_synthetic
    )
