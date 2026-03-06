"""
Core boxing analysis engine.
Evaluates video based on boxing fundamentals and provides structured feedback.
"""

import numpy as np
from pose_estimator import (
    compute_boxing_angles, detect_stance, compute_frame_features,
    LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_WRIST, RIGHT_WRIST,
    LEFT_ELBOW, RIGHT_ELBOW, LEFT_HIP, RIGHT_HIP,
    LEFT_KNEE, RIGHT_KNEE, LEFT_ANKLE, RIGHT_ANKLE, NOSE
)
from fighter_presets import match_style_to_presets

# Move labels the classifier recognizes
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


def analyze_sequence(all_landmarks, move_predictions=None):
    """Perform full boxing analysis on a sequence of pose landmarks.

    Args:
        all_landmarks: List of (frame_idx, landmarks_array) tuples from pose_estimator.
        move_predictions: Optional list of predicted move labels per frame window.

    Returns:
        dict with complete analysis results.
    """
    if not all_landmarks:
        return {"error": "No poses detected in the video."}

    # Compute per-frame metrics
    frame_angles = []
    stances = []
    guard_scores = []
    balance_scores = []
    head_positions = []

    for frame_idx, landmarks in all_landmarks:
        angles = compute_boxing_angles(landmarks)
        frame_angles.append(angles)
        stances.append(detect_stance(landmarks))

        guard = _evaluate_guard(landmarks, angles)
        guard_scores.append(guard)

        balance = _evaluate_balance(landmarks)
        balance_scores.append(balance)

        head_positions.append(landmarks[NOSE][:2].copy())

    # Aggregate metrics
    stance_analysis = _analyze_stance_consistency(stances)
    guard_analysis = _analyze_guard(guard_scores, frame_angles)
    footwork_analysis = _analyze_footwork(all_landmarks)
    head_movement_analysis = _analyze_head_movement(head_positions)
    balance_analysis = _aggregate_balance(balance_scores)
    punch_analysis = _analyze_punches(move_predictions) if move_predictions else None

    # Compute overall traits for style matching
    traits = _compute_style_traits(
        guard_analysis, footwork_analysis, head_movement_analysis,
        balance_analysis, punch_analysis, frame_angles
    )

    # Match against fighter presets
    style_matches = match_style_to_presets(traits)
    top_styles = [
        {
            "fighter": m[2]["name"],
            "nickname": m[2]["nickname"],
            "similarity": m[1],
            "style": m[2]["style"],
            "description": m[2]["description"],
        }
        for m in style_matches[:3]
    ]

    # Generate feedback
    strengths, improvements = _generate_feedback(
        stance_analysis, guard_analysis, footwork_analysis,
        head_movement_analysis, balance_analysis, punch_analysis
    )

    # Overall score (weighted fundamentals)
    overall_score = _compute_overall_score(
        guard_analysis, footwork_analysis, head_movement_analysis,
        balance_analysis, punch_analysis
    )

    return {
        "overall_score": round(overall_score, 1),
        "stance": stance_analysis,
        "guard": guard_analysis,
        "footwork": footwork_analysis,
        "head_movement": head_movement_analysis,
        "balance": balance_analysis,
        "punches": punch_analysis,
        "style_traits": traits,
        "style_matches": top_styles,
        "strengths": strengths,
        "improvements": improvements,
        "frames_analyzed": len(all_landmarks),
    }


def _evaluate_guard(landmarks, angles):
    """Score guard quality for a single frame (0-1)."""
    # Good guard: hands near chin level, elbows tucked
    left_guard = angles["left_guard_height"]
    right_guard = angles["right_guard_height"]

    # Ideal: wrists at or slightly above nose level (guard_height ~ 0 or slightly negative)
    left_score = max(0, 1.0 - abs(left_guard) * 3)
    right_score = max(0, 1.0 - abs(right_guard) * 3)

    # Elbow tuck: elbows should be somewhat bent (angle 30-90)
    left_elbow = angles["left_elbow"]
    right_elbow = angles["right_elbow"]
    left_tuck = 1.0 if 30 <= left_elbow <= 100 else max(0, 1.0 - abs(left_elbow - 65) / 90)
    right_tuck = 1.0 if 30 <= right_elbow <= 100 else max(0, 1.0 - abs(right_elbow - 65) / 90)

    return {
        "hand_position": (left_score + right_score) / 2,
        "elbow_tuck": (left_tuck + right_tuck) / 2,
        "overall": (left_score + right_score + left_tuck + right_tuck) / 4,
    }


def _evaluate_balance(landmarks):
    """Score balance for a single frame (0-1)."""
    # Balance: shoulder center should be roughly over hip center
    shoulder_center = (landmarks[LEFT_SHOULDER][:2] + landmarks[RIGHT_SHOULDER][:2]) / 2
    hip_center = (landmarks[LEFT_HIP][:2] + landmarks[RIGHT_HIP][:2]) / 2

    offset = np.linalg.norm(shoulder_center - hip_center)
    score = max(0, 1.0 - offset * 5)

    # Weight distribution: knees should be reasonably bent
    left_knee_y = landmarks[LEFT_KNEE][1]
    right_knee_y = landmarks[RIGHT_KNEE][1]
    knee_diff = abs(left_knee_y - right_knee_y)
    knee_score = max(0, 1.0 - knee_diff * 10)

    return {"center_of_gravity": score, "weight_distribution": knee_score, "overall": (score + knee_score) / 2}


def _analyze_stance_consistency(stances):
    """Analyze stance consistency across frames."""
    if not stances:
        return {"dominant": "unknown", "consistency": 0}

    from collections import Counter
    counts = Counter(stances)
    dominant = counts.most_common(1)[0]
    consistency = dominant[1] / len(stances)

    return {
        "dominant": dominant[0],
        "consistency": round(consistency * 100, 1),
        "breakdown": {k: round(v / len(stances) * 100, 1) for k, v in counts.items()},
        "score": round(consistency * 100, 1),
    }


def _analyze_guard(guard_scores, frame_angles):
    """Aggregate guard analysis across all frames."""
    if not guard_scores:
        return {"score": 0, "hand_position": 0, "elbow_tuck": 0}

    avg_hand = np.mean([g["hand_position"] for g in guard_scores])
    avg_tuck = np.mean([g["elbow_tuck"] for g in guard_scores])
    avg_overall = np.mean([g["overall"] for g in guard_scores])

    # Guard consistency: how often does the guard drop?
    guard_drops = sum(1 for g in guard_scores if g["hand_position"] < 0.3)
    drop_rate = guard_drops / len(guard_scores)

    return {
        "score": round(avg_overall * 100, 1),
        "hand_position": round(avg_hand * 100, 1),
        "elbow_tuck": round(avg_tuck * 100, 1),
        "guard_drop_rate": round(drop_rate * 100, 1),
        "consistency": round((1 - drop_rate) * 100, 1),
    }


def _analyze_footwork(all_landmarks):
    """Analyze footwork quality: movement, stance width, lateral movement."""
    if len(all_landmarks) < 2:
        return {"score": 50, "lateral_movement": 0, "stance_width_consistency": 0}

    foot_positions = []
    stance_widths = []

    for _, landmarks in all_landmarks:
        left_foot = landmarks[LEFT_ANKLE][:2]
        right_foot = landmarks[RIGHT_ANKLE][:2]
        center = (left_foot + right_foot) / 2
        foot_positions.append(center)
        stance_widths.append(np.linalg.norm(left_foot - right_foot))

    foot_positions = np.array(foot_positions)

    # Movement amount
    if len(foot_positions) > 1:
        deltas = np.diff(foot_positions, axis=0)
        movements = np.linalg.norm(deltas, axis=1)
        lateral_deltas = np.abs(deltas[:, 0])  # X-axis movement
        forward_deltas = np.abs(deltas[:, 1])  # Y-axis movement

        total_movement = np.sum(movements)
        lateral_ratio = np.sum(lateral_deltas) / (total_movement + 1e-8)
    else:
        total_movement = 0
        lateral_ratio = 0

    # Stance width consistency
    width_std = np.std(stance_widths)
    width_consistency = max(0, 1.0 - width_std * 10)

    # Score: good footwork = consistent stance width + purposeful movement
    movement_score = min(1.0, total_movement * 10)  # Some movement is good
    score = (width_consistency * 0.4 + movement_score * 0.3 + lateral_ratio * 0.3)

    return {
        "score": round(score * 100, 1),
        "lateral_movement": round(lateral_ratio * 100, 1),
        "stance_width_consistency": round(width_consistency * 100, 1),
        "total_movement": round(total_movement, 4),
    }


def _analyze_head_movement(head_positions):
    """Analyze head movement — good boxers move their head off the center line."""
    if len(head_positions) < 2:
        return {"score": 50, "variation": 0}

    positions = np.array(head_positions)
    x_std = np.std(positions[:, 0])
    y_std = np.std(positions[:, 1])

    # Good head movement shows variation in both X and Y
    variation = (x_std + y_std) / 2
    # Normalize: some variation is good, too much might be erratic
    score = min(1.0, variation * 15)

    return {
        "score": round(score * 100, 1),
        "horizontal_variation": round(x_std * 100, 4),
        "vertical_variation": round(y_std * 100, 4),
    }


def _aggregate_balance(balance_scores):
    """Aggregate balance scores."""
    if not balance_scores:
        return {"score": 50}

    avg_cog = np.mean([b["center_of_gravity"] for b in balance_scores])
    avg_weight = np.mean([b["weight_distribution"] for b in balance_scores])
    avg_overall = np.mean([b["overall"] for b in balance_scores])

    return {
        "score": round(avg_overall * 100, 1),
        "center_of_gravity": round(avg_cog * 100, 1),
        "weight_distribution": round(avg_weight * 100, 1),
    }


def _analyze_punches(move_predictions):
    """Analyze punch distribution and technique from move predictions."""
    if not move_predictions:
        return None

    from collections import Counter
    counts = Counter(move_predictions)
    total = len(move_predictions)

    punch_types = ["jab", "cross", "lead_hook", "rear_hook", "lead_uppercut", "rear_uppercut"]
    defense_types = ["slip_left", "slip_right", "bob_and_weave", "block"]

    total_punches = sum(counts.get(p, 0) for p in punch_types)
    total_defense = sum(counts.get(d, 0) for d in defense_types)

    distribution = {move: round(counts.get(move, 0) / total * 100, 1) for move in MOVE_LABELS}

    # Variety score: how many different techniques are used
    used_types = sum(1 for m in MOVE_LABELS if counts.get(m, 0) > 0)
    variety = used_types / len(MOVE_LABELS)

    # Jab ratio: good boxers throw a high percentage of jabs
    jab_ratio = counts.get("jab", 0) / (total_punches + 1e-8)

    return {
        "total_punches": total_punches,
        "total_defensive_moves": total_defense,
        "distribution": distribution,
        "variety_score": round(variety * 100, 1),
        "jab_ratio": round(jab_ratio * 100, 1),
        "punch_defense_ratio": round(total_punches / (total_defense + 1e-8), 2),
    }


def _compute_style_traits(guard, footwork, head_movement, balance, punches, frame_angles):
    """Compute normalized style traits for fighter preset matching."""
    traits = {}

    traits["head_movement"] = min(1.0, (head_movement.get("score", 50)) / 100)
    traits["guard_tightness"] = min(1.0, guard.get("score", 50) / 100)
    traits["footwork_lateral"] = min(1.0, footwork.get("lateral_movement", 50) / 100)
    traits["footwork_forward"] = min(1.0, max(0, 1.0 - footwork.get("lateral_movement", 50) / 100))
    traits["distance_control"] = min(1.0, footwork.get("stance_width_consistency", 50) / 100)

    # Crouch level from average knee angles
    if frame_angles:
        avg_left_knee = np.mean([a["left_knee"] for a in frame_angles])
        avg_right_knee = np.mean([a["right_knee"] for a in frame_angles])
        avg_knee = (avg_left_knee + avg_right_knee) / 2
        # Lower angle = more bent = more crouch
        traits["crouch_level"] = max(0, 1.0 - avg_knee / 180)
    else:
        traits["crouch_level"] = 0.5

    if punches:
        traits["jab_usage"] = min(1.0, punches.get("jab_ratio", 0) / 100)
        traits["combination_frequency"] = min(1.0, punches.get("variety_score", 0) / 100)
        traits["aggression"] = min(1.0, punches.get("punch_defense_ratio", 1) / 5)
        traits["counter_punching"] = min(1.0, punches.get("total_defensive_moves", 0) / 20)
        traits["body_work"] = 0.5  # Can't easily detect from pose alone
        traits["punch_power"] = 0.5  # Can't detect from pose
        traits["punch_speed"] = 0.5  # Would need temporal analysis
        traits["ring_cutting"] = traits["footwork_forward"]
    else:
        traits["jab_usage"] = 0.5
        traits["combination_frequency"] = 0.5
        traits["aggression"] = 0.5
        traits["counter_punching"] = 0.5
        traits["body_work"] = 0.5
        traits["punch_power"] = 0.5
        traits["punch_speed"] = 0.5
        traits["ring_cutting"] = 0.5

    return traits


def _compute_overall_score(guard, footwork, head_movement, balance, punches):
    """Compute weighted overall score."""
    weights = {
        "guard": 0.25,
        "footwork": 0.20,
        "head_movement": 0.20,
        "balance": 0.15,
        "punches": 0.20,
    }

    scores = {
        "guard": guard.get("score", 50),
        "footwork": footwork.get("score", 50),
        "head_movement": head_movement.get("score", 50),
        "balance": balance.get("score", 50),
    }

    if punches:
        scores["punches"] = punches.get("variety_score", 50)
    else:
        scores["punches"] = 50
        weights["guard"] = 0.30
        weights["footwork"] = 0.25
        weights["head_movement"] = 0.25
        weights["balance"] = 0.20
        weights["punches"] = 0.0

    total = sum(scores[k] * weights[k] for k in weights)
    return total


def _generate_feedback(stance, guard, footwork, head_movement, balance, punches):
    """Generate human-readable strengths and improvement suggestions."""
    strengths = []
    improvements = []

    # Stance
    if stance.get("consistency", 0) > 80:
        strengths.append(f"Consistent {stance['dominant']} stance ({stance['consistency']}% of frames)")
    elif stance.get("consistency", 0) < 50:
        improvements.append(
            "Work on maintaining a consistent stance. You switch between stances frequently, "
            "which can leave you off-balance."
        )

    # Guard
    guard_score = guard.get("score", 0)
    if guard_score > 70:
        strengths.append(f"Strong guard positioning (score: {guard_score}/100)")
    if guard_score < 50:
        improvements.append(
            "Your guard needs work. Keep your hands up near your chin and your elbows tucked "
            "to protect your body. A dropped guard leaves you vulnerable to counters."
        )
    if guard.get("guard_drop_rate", 0) > 30:
        improvements.append(
            f"Your guard drops {guard['guard_drop_rate']}% of the time. Focus on returning "
            "your hands to guard position after every punch."
        )
    if guard.get("elbow_tuck", 0) > 75:
        strengths.append("Good elbow tucking — protecting the body well")

    # Footwork
    footwork_score = footwork.get("score", 0)
    if footwork_score > 70:
        strengths.append(f"Good footwork with purposeful movement (score: {footwork_score}/100)")
    if footwork.get("lateral_movement", 0) > 40:
        strengths.append("Good lateral movement — makes you harder to hit")
    if footwork.get("lateral_movement", 0) < 15:
        improvements.append(
            "Add more lateral movement to your footwork. Moving side-to-side makes you a harder "
            "target and creates better angles for attack."
        )
    if footwork.get("stance_width_consistency", 0) < 50:
        improvements.append(
            "Maintain a more consistent stance width. Your feet are changing distance too much, "
            "which affects your balance and power generation."
        )

    # Head movement
    head_score = head_movement.get("score", 0)
    if head_score > 70:
        strengths.append(f"Active head movement (score: {head_score}/100)")
    if head_score < 30:
        improvements.append(
            "Your head stays too stationary. Practice slipping, bobbing, and weaving to make "
            "yourself a moving target. A still head is an easy target."
        )

    # Balance
    balance_score = balance.get("score", 0)
    if balance_score > 75:
        strengths.append(f"Excellent balance and weight distribution (score: {balance_score}/100)")
    if balance_score < 45:
        improvements.append(
            "Work on your balance. Keep your weight centered and your knees slightly bent. "
            "Good balance is the foundation of both offense and defense."
        )

    # Punches
    if punches:
        if punches.get("variety_score", 0) > 60:
            strengths.append("Good punch variety — using multiple techniques effectively")
        if punches.get("variety_score", 0) < 30:
            improvements.append(
                "Diversify your punch selection. You're relying too heavily on a small number "
                "of techniques. Mix in hooks, uppercuts, and body shots."
            )
        if punches.get("jab_ratio", 0) > 30:
            strengths.append(f"Good jab usage ({punches['jab_ratio']}%) — the jab is the most important punch")
        elif punches.get("jab_ratio", 0) < 15 and punches.get("total_punches", 0) > 5:
            improvements.append(
                "Use your jab more. It's the most important punch in boxing — it sets up "
                "combinations, controls distance, and keeps your opponent honest."
            )
        if punches.get("total_defensive_moves", 0) < 3 and punches.get("total_punches", 0) > 10:
            improvements.append(
                "Incorporate more defensive movements. Boxing isn't just about offense — "
                "slipping, blocking, and weaving are crucial for longevity."
            )

    # Ensure at least one of each
    if not strengths:
        strengths.append("Keep training! Every session builds your foundation.")
    if not improvements:
        improvements.append("Looking solid overall. Continue refining your technique and speed.")

    return strengths, improvements
