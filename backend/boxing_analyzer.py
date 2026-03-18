"""
Core boxing analysis engine.
Evaluates video based on boxing fundamentals and provides structured,
analytical feedback with reasoning chains. Supports multi-fighter analysis
with opponent-aware coaching, timestamp references, combination detection,
and punch mechanics evaluation.
"""

import numpy as np
from collections import Counter
from pose_estimator import (
    compute_boxing_angles, detect_stance, compute_frame_features,
    LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_WRIST, RIGHT_WRIST,
    LEFT_ELBOW, RIGHT_ELBOW, LEFT_HIP, RIGHT_HIP,
    LEFT_KNEE, RIGHT_KNEE, LEFT_ANKLE, RIGHT_ANKLE, NOSE
)
from fighter_presets import match_style_to_presets
from boxing_knowledge import (
    GUARD_TYPES, STANCES, GUARD_FEEDBACK, STANCE_FEEDBACK,
    SCORE_INTERPRETATIONS, COMBINATION_PATTERNS, COUNTER_OPPORTUNITIES,
    PUNCH_MECHANICS_CRITERIA, DRILL_RECOMMENDATIONS,
    build_guard_reasoning, build_stance_reasoning,
    get_score_interpretation, build_improvement_plan, get_drills_for_weakness,
)

# Move labels the classifier recognizes
MOVE_LABELS = [
    "jab", "cross", "lead_hook", "rear_hook",
    "lead_uppercut", "rear_uppercut",
    "slip_left", "slip_right", "bob_and_weave", "block",
    "idle_guard", "footwork"
]

PUNCH_LABELS = {"jab", "cross", "lead_hook", "rear_hook", "lead_uppercut", "rear_uppercut"}
DEFENSE_LABELS = {"slip_left", "slip_right", "bob_and_weave", "block"}


def _format_timestamp(frame_idx, video_fps):
    """Convert a frame index to a human-readable timestamp string."""
    if video_fps <= 0:
        video_fps = 30.0
    seconds = frame_idx / video_fps
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}:{secs:04.1f}"


# -------------------------------------------------------------------
# Main entry points
# -------------------------------------------------------------------

def analyze_sequence(all_landmarks, move_predictions=None, video_fps=30.0):
    """Perform full boxing analysis on a sequence of pose landmarks.

    Args:
        all_landmarks: List of (frame_idx, landmarks_array) tuples.
        move_predictions: List of dicts with label, confidence, frame_idx, frame_end.
        video_fps: Video FPS for timestamp calculation.

    Returns dict with complete analysis results including detailed
    analytical commentary and event timeline.
    """
    if not all_landmarks:
        return {"error": "No poses detected in the video."}

    # Compute per-frame metrics
    frame_angles = []
    stances = []
    guard_scores = []
    balance_scores = []
    head_positions = []
    event_timeline = []

    for frame_idx, landmarks in all_landmarks:
        angles = compute_boxing_angles(landmarks)
        frame_angles.append(angles)
        stances.append(detect_stance(landmarks))

        guard = _evaluate_guard(landmarks, angles)
        guard_scores.append(guard)

        balance = _evaluate_balance(landmarks)
        balance_scores.append(balance)

        head_positions.append(landmarks[NOSE][:2].copy())

        # Detect guard drop events with timestamps
        if guard["hand_position"] < 0.25:
            event_timeline.append({
                "type": "guard_drop",
                "frame_idx": frame_idx,
                "timestamp": _format_timestamp(frame_idx, video_fps),
                "detail": "Guard dropped significantly — head exposed",
            })

    # Aggregate metrics
    stance_analysis = _analyze_stance_consistency(stances)
    guard_analysis = _analyze_guard(guard_scores, frame_angles)
    guard_type = _detect_guard_type(guard_scores, frame_angles)
    guard_analysis["guard_type"] = guard_type
    footwork_analysis = _analyze_footwork(all_landmarks)
    head_movement_analysis = _analyze_head_movement(head_positions)
    balance_analysis = _aggregate_balance(balance_scores)

    # Punch analysis with timestamps
    punch_analysis = None
    combination_analysis = None
    punch_mechanics = None
    if move_predictions:
        punch_analysis = _analyze_punches(move_predictions, video_fps)
        combination_analysis = _detect_combinations(move_predictions, video_fps)
        punch_mechanics = _analyze_punch_mechanics(
            all_landmarks, move_predictions, frame_angles, video_fps
        )

        # Add punch events to timeline
        for pred in move_predictions:
            if pred["label"] in PUNCH_LABELS:
                event_timeline.append({
                    "type": "punch",
                    "frame_idx": pred["frame_idx"],
                    "timestamp": _format_timestamp(pred["frame_idx"], video_fps),
                    "detail": f"{pred['label'].replace('_', ' ').title()} thrown (confidence: {pred['confidence']:.0%})",
                    "move": pred["label"],
                })
            elif pred["label"] in DEFENSE_LABELS:
                event_timeline.append({
                    "type": "defense",
                    "frame_idx": pred["frame_idx"],
                    "timestamp": _format_timestamp(pred["frame_idx"], video_fps),
                    "detail": f"{pred['label'].replace('_', ' ').title()} detected",
                    "move": pred["label"],
                })

    # Sort timeline by frame index
    event_timeline.sort(key=lambda e: e["frame_idx"])

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

    # Generate basic strengths/improvements lists
    strengths, improvements = _generate_feedback(
        stance_analysis, guard_analysis, footwork_analysis,
        head_movement_analysis, balance_analysis, punch_analysis
    )

    # Overall score (weighted fundamentals)
    overall_score = _compute_overall_score(
        guard_analysis, footwork_analysis, head_movement_analysis,
        balance_analysis, punch_analysis
    )

    # Build detailed analytical commentary
    detailed = _build_detailed_analysis(
        overall_score, stance_analysis, guard_analysis, guard_type,
        footwork_analysis, head_movement_analysis, balance_analysis,
        punch_analysis, top_styles, combination_analysis, punch_mechanics
    )

    return {
        "overall_score": round(overall_score, 1),
        "stance": stance_analysis,
        "guard": guard_analysis,
        "footwork": footwork_analysis,
        "head_movement": head_movement_analysis,
        "balance": balance_analysis,
        "punches": punch_analysis,
        "combinations": combination_analysis,
        "punch_mechanics": punch_mechanics,
        "style_traits": traits,
        "style_matches": top_styles,
        "strengths": strengths,
        "improvements": improvements,
        "detailed_analysis": detailed,
        "event_timeline": event_timeline,
        "frames_analyzed": len(all_landmarks),
    }


def analyze_both_fighters(fighter_a_landmarks, fighter_b_landmarks,
                          move_preds_a, move_preds_b, video_fps=30.0):
    """Analyze both fighters and cross-reference for opponent-aware coaching.

    Args:
        fighter_a_landmarks: List of (frame_idx, landmarks) for fighter A.
        fighter_b_landmarks: List of (frame_idx, landmarks) for fighter B.
        move_preds_a: Move predictions for fighter A.
        move_preds_b: Move predictions for fighter B.
        video_fps: Video FPS.

    Returns:
        dict with keys "fighter_a" and "fighter_b", each containing full
        analysis plus opponent_patterns section.
    """
    analysis_a = analyze_sequence(fighter_a_landmarks, move_preds_a, video_fps)
    analysis_b = analyze_sequence(fighter_b_landmarks, move_preds_b, video_fps)

    # Cross-reference: generate opponent-aware feedback for each fighter
    analysis_a["opponent_patterns"] = _generate_opponent_coaching(
        analysis_a, analysis_b, move_preds_b, video_fps, "your opponent"
    )
    analysis_b["opponent_patterns"] = _generate_opponent_coaching(
        analysis_b, analysis_a, move_preds_a, video_fps, "your opponent"
    )

    return {
        "fighter_a": analysis_a,
        "fighter_b": analysis_b,
    }


# -------------------------------------------------------------------
# Opponent-aware coaching
# -------------------------------------------------------------------

def _generate_opponent_coaching(my_analysis, opp_analysis, opp_predictions,
                                video_fps, opp_label="your opponent"):
    """Generate coaching advice based on opponent's patterns and weaknesses."""
    patterns = []

    opp_guard = opp_analysis.get("guard", {})
    opp_punches = opp_analysis.get("punches", {})
    opp_head = opp_analysis.get("head_movement", {})
    opp_timeline = opp_analysis.get("event_timeline", [])

    # Check for opponent guard drops
    guard_drops = [e for e in opp_timeline if e["type"] == "guard_drop"]
    if len(guard_drops) >= 2:
        timestamps = ", ".join(e["timestamp"] for e in guard_drops[:5])
        patterns.append({
            "type": "exploitable_habit",
            "title": "Opponent drops guard frequently",
            "description": (
                f"{opp_label.title()} dropped their guard {len(guard_drops)} times "
                f"(at {timestamps}). Attack with straight punches to the head "
                f"when you see the guard drop — a quick 1-2 (jab-cross) is ideal."
            ),
            "counter_advice": COUNTER_OPPORTUNITIES["low_guard_habit"]["counter"],
        })

    # Check if opponent has a high guard drop rate
    if opp_guard.get("guard_drop_rate", 0) > 30:
        patterns.append({
            "type": "exploitable_habit",
            "title": f"Opponent's guard drops in {opp_guard['guard_drop_rate']:.0f}% of frames",
            "description": (
                f"{opp_label.title()} is inconsistent with their guard — it drops in "
                f"{opp_guard['guard_drop_rate']:.0f}% of frames. Time your attacks for "
                f"moments when their hands drop below chin level."
            ),
            "counter_advice": "Use feints to draw out the guard drop, then attack.",
        })

    # Check opponent's punch patterns for counter opportunities
    if opp_predictions:
        opp_punch_events = [p for p in opp_predictions if p["label"] in PUNCH_LABELS]

        # Detect if opponent drops guard after specific punches
        _check_post_punch_guard_drops(
            opp_punch_events, opp_timeline, patterns, video_fps, opp_label
        )

        # Check opponent's punch variety
        opp_punch_counts = Counter(p["label"] for p in opp_punch_events)
        if opp_punch_counts:
            most_common_punch = opp_punch_counts.most_common(1)[0]
            total_opp_punches = sum(opp_punch_counts.values())
            if total_opp_punches > 3:
                pct = most_common_punch[1] / total_opp_punches * 100
                if pct > 50:
                    punch_name = most_common_punch[0].replace("_", " ").title()
                    patterns.append({
                        "type": "predictable_offense",
                        "title": f"Opponent relies heavily on {punch_name} ({pct:.0f}%)",
                        "description": (
                            f"{opp_label.title()} throws {punch_name} {pct:.0f}% of the time. "
                            f"This is predictable — prepare your defense specifically for this "
                            f"punch and look to counter after they throw it."
                        ),
                        "counter_advice": f"Anticipate the {punch_name} and have your counter ready.",
                    })

    # Check opponent's head movement
    if opp_head.get("score", 50) < 30:
        patterns.append({
            "type": "exploitable_weakness",
            "title": "Opponent has minimal head movement",
            "description": (
                f"{opp_label.title()}'s head stays on the centre line "
                f"(head movement score: {opp_head.get('score', 0):.0f}/100). "
                f"They are easy to time with straight punches. Use feints to "
                f"freeze them, then attack."
            ),
            "counter_advice": COUNTER_OPPORTUNITIES["static_head"]["counter"],
        })

    # Check opponent's footwork for retreating patterns
    opp_footwork = opp_analysis.get("footwork", {})
    if opp_footwork.get("lateral_movement", 50) < 15:
        patterns.append({
            "type": "exploitable_weakness",
            "title": "Opponent moves mostly forward and back",
            "description": (
                f"{opp_label.title()} has minimal lateral movement "
                f"({opp_footwork.get('lateral_movement', 0):.0f}%). "
                f"Cut off the ring by stepping to the side when they retreat. "
                f"They're predictable in their movement direction."
            ),
            "counter_advice": COUNTER_OPPORTUNITIES["retreats_straight_back"]["counter"],
        })

    if not patterns:
        patterns.append({
            "type": "general",
            "title": "No obvious exploitable patterns detected",
            "description": (
                f"{opp_label.title()} doesn't show obvious exploitable habits "
                f"in this footage. Focus on your own fundamentals and look "
                f"for opportunities in real-time."
            ),
            "counter_advice": "Stay disciplined and wait for openings.",
        })

    return patterns


def _check_post_punch_guard_drops(punch_events, timeline, patterns,
                                   video_fps, opp_label):
    """Detect if opponent drops guard after throwing specific punches."""
    guard_drop_frames = {e["frame_idx"] for e in timeline if e["type"] == "guard_drop"}

    punch_type_drops = {}
    for punch in punch_events:
        # Check if guard drops within ~0.5 seconds after the punch
        check_window = int(video_fps * 0.5)
        for f in range(punch["frame_end"], punch["frame_end"] + check_window):
            if f in guard_drop_frames:
                ptype = punch["label"]
                if ptype not in punch_type_drops:
                    punch_type_drops[ptype] = []
                punch_type_drops[ptype].append(
                    _format_timestamp(punch["frame_idx"], video_fps)
                )
                break

    for ptype, timestamps in punch_type_drops.items():
        if len(timestamps) >= 2:
            punch_name = ptype.replace("_", " ").title()
            ts_str = ", ".join(timestamps[:5])
            key = f"drops_guard_after_{ptype.split('_')[-1]}"
            counter = COUNTER_OPPORTUNITIES.get(
                key, COUNTER_OPPORTUNITIES.get("drops_guard_between_combos", {})
            )
            patterns.append({
                "type": "exploitable_habit",
                "title": f"Opponent drops guard after {punch_name}",
                "description": (
                    f"{opp_label.title()} drops their guard after throwing a "
                    f"{punch_name} (observed at {ts_str}). Counter with a quick "
                    f"punch immediately after they throw."
                ),
                "counter_advice": counter.get("counter", "Counter immediately after their punch."),
            })


# -------------------------------------------------------------------
# Combination detection
# -------------------------------------------------------------------

def _detect_combinations(move_predictions, video_fps):
    """Detect punch combinations from sequential move predictions.

    Returns dict with detected combinations, flow score, and recommendations.
    """
    if not move_predictions:
        return None

    punch_sequence = []
    for pred in move_predictions:
        if pred["label"] in PUNCH_LABELS:
            punch_sequence.append(pred)

    if len(punch_sequence) < 2:
        return {
            "detected_combinations": [],
            "flow_score": 0,
            "total_combinations": 0,
            "recommendations": ["Throw more combinations — single punches are easier to defend against."],
        }

    # Group consecutive punches into combinations (within 1 second of each other)
    max_gap_frames = int(video_fps * 1.0)
    combos = []
    current_combo = [punch_sequence[0]]

    for i in range(1, len(punch_sequence)):
        gap = punch_sequence[i]["frame_idx"] - punch_sequence[i - 1]["frame_end"]
        if gap <= max_gap_frames:
            current_combo.append(punch_sequence[i])
        else:
            if len(current_combo) >= 2:
                combos.append(current_combo)
            current_combo = [punch_sequence[i]]

    if len(current_combo) >= 2:
        combos.append(current_combo)

    # Analyze detected combinations
    detected = []
    for combo in combos:
        labels = [p["label"] for p in combo]
        start_ts = _format_timestamp(combo[0]["frame_idx"], video_fps)
        end_ts = _format_timestamp(combo[-1]["frame_end"], video_fps)

        # Try to match against known patterns
        matched_pattern = _match_combination_pattern(labels)
        combo_name = matched_pattern["name"] if matched_pattern else " - ".join(
            l.replace("_", " ").title() for l in labels
        )

        detected.append({
            "punches": labels,
            "name": combo_name,
            "start_timestamp": start_ts,
            "end_timestamp": end_ts,
            "punch_count": len(labels),
            "known_pattern": matched_pattern is not None,
        })

    # Score combination flow
    flow_score = _score_combination_flow(combos, punch_sequence)

    # Generate recommendations
    recommendations = _combo_recommendations(combos, punch_sequence, detected)

    return {
        "detected_combinations": detected,
        "flow_score": round(flow_score, 1),
        "total_combinations": len(detected),
        "total_single_punches": len(punch_sequence) - sum(len(c) for c in combos),
        "recommendations": recommendations,
    }


def _match_combination_pattern(labels):
    """Try to match a punch sequence against known combination patterns."""
    for pattern_key, pattern in COMBINATION_PATTERNS.items():
        pattern_seq = pattern["sequence"]
        if len(labels) >= len(pattern_seq):
            # Check if the pattern appears as a subsequence
            for start in range(len(labels) - len(pattern_seq) + 1):
                if labels[start:start + len(pattern_seq)] == pattern_seq:
                    return pattern
    return None


def _score_combination_flow(combos, all_punches):
    """Score how well combinations flow (0-100)."""
    if not all_punches:
        return 0

    total_punches = len(all_punches)
    punches_in_combos = sum(len(c) for c in combos)
    combo_ratio = punches_in_combos / total_punches if total_punches > 0 else 0

    # Bonus for known patterns
    known_pattern_count = 0
    for combo in combos:
        labels = [p["label"] for p in combo]
        if _match_combination_pattern(labels):
            known_pattern_count += 1

    pattern_bonus = min(20, known_pattern_count * 10)

    # Bonus for variety in combinations
    combo_types = set()
    for combo in combos:
        combo_types.add(tuple(p["label"] for p in combo))
    variety_bonus = min(15, len(combo_types) * 5)

    score = combo_ratio * 65 + pattern_bonus + variety_bonus
    return min(100, score)


def _combo_recommendations(combos, all_punches, detected):
    """Generate combination-specific recommendations."""
    recs = []
    total_punches = len(all_punches)
    punches_in_combos = sum(len(c) for c in combos)

    if total_punches > 0:
        single_ratio = (total_punches - punches_in_combos) / total_punches
        if single_ratio > 0.7:
            recs.append(
                "You're throwing too many single punches. Combinations are harder to "
                "defend against. Start with basic 1-2s (jab-cross) and build from there."
            )

    if combos:
        avg_length = sum(len(c) for c in combos) / len(combos)
        if avg_length < 2.5:
            recs.append(
                "Your combinations are short (mostly 2 punches). Try extending to "
                "3-4 punch combinations like 1-2-3 (jab-cross-hook) for more scoring "
                "opportunities."
            )

    # Check for setup punches
    if all_punches:
        first_punches = Counter(c[0]["label"] for c in combos) if combos else Counter()
        total_combos = len(combos)
        if total_combos > 0:
            jab_opens = first_punches.get("jab", 0) / total_combos
            if jab_opens < 0.3:
                recs.append(
                    "Use the jab to set up your combinations. Only "
                    f"{jab_opens:.0%} of your combinations start with a jab — "
                    "the jab is the best setup punch in boxing."
                )

    if not combos and total_punches > 5:
        recs.append(
            "No combinations detected. You need to connect your punches into "
            "flowing combinations. Drill: 1-2 on the bag for 3 rounds, "
            "then 1-2-3, then 1-2-3-2."
        )

    if not recs:
        recs.append("Good combination work. Continue developing your combination variety.")

    return recs


# -------------------------------------------------------------------
# Punch mechanics analysis
# -------------------------------------------------------------------

def _analyze_punch_mechanics(all_landmarks, move_predictions, frame_angles, video_fps):
    """Analyze the biomechanics of detected punches.

    Evaluates hip rotation, arm extension, guard discipline during punches,
    and snap-back speed.
    """
    if not move_predictions:
        return None

    punch_preds = [p for p in move_predictions if p["label"] in PUNCH_LABELS]
    if not punch_preds:
        return None

    # Build frame_idx -> index mapping for landmark lookup
    frame_map = {fidx: i for i, (fidx, _) in enumerate(all_landmarks)}

    mechanics_by_type = {}

    for pred in punch_preds:
        punch_type = pred["label"]
        criteria = PUNCH_MECHANICS_CRITERIA.get(punch_type)
        if not criteria:
            continue

        # Find the frame data for this punch
        fidx = pred["frame_idx"]
        if fidx not in frame_map:
            continue
        idx = frame_map[fidx]
        _, landmarks = all_landmarks[idx]
        angles = frame_angles[idx] if idx < len(frame_angles) else None
        if angles is None:
            continue

        # Evaluate mechanics
        is_left = punch_type.startswith("lead") or punch_type == "jab"

        if is_left:
            elbow_angle = angles["left_elbow"]
            shoulder_angle = angles["left_shoulder"]
            guard_hand_height = angles["right_guard_height"]
        else:
            elbow_angle = angles["right_elbow"]
            shoulder_angle = angles["right_shoulder"]
            guard_hand_height = angles["left_guard_height"]

        # Score extension
        ideal_ext = criteria["ideal_elbow_extension"]
        ext_score = _range_score(elbow_angle, ideal_ext[0], ideal_ext[1])

        # Score shoulder engagement
        ideal_sh = criteria["ideal_shoulder_angle"]
        sh_score = _range_score(shoulder_angle, ideal_sh[0], ideal_sh[1])

        # Score rear hand discipline (did guard stay up?)
        guard_discipline = max(0, 1.0 - abs(guard_hand_height) * 3)

        # Check hip rotation (compare hip angles)
        hip_rotation_score = 0.5
        if idx > 0 and idx < len(frame_angles):
            prev_angles = frame_angles[idx - 1] if idx > 0 else angles
            hip_delta = abs(
                angles["left_hip"] - prev_angles["left_hip"]
            ) + abs(
                angles["right_hip"] - prev_angles["right_hip"]
            )
            if criteria["hip_rotation_expected"] == "significant":
                hip_rotation_score = min(1.0, hip_delta / 20)
            elif criteria["hip_rotation_expected"] == "moderate":
                hip_rotation_score = min(1.0, hip_delta / 15)
            else:
                hip_rotation_score = 0.7  # minimal rotation expected

        # Check snap-back (how quickly guard returns after punch)
        snap_back_score = 0.5
        if idx + 1 < len(frame_angles):
            next_angles = frame_angles[idx + 1]
            if is_left:
                next_elbow = next_angles["left_elbow"]
            else:
                next_elbow = next_angles["right_elbow"]
            # If elbow returns to bent (< 120), good snap-back
            if next_elbow < 120:
                snap_back_score = 0.9
            elif next_elbow < 140:
                snap_back_score = 0.6
            else:
                snap_back_score = 0.3

        overall_mech = (ext_score * 0.25 + sh_score * 0.2 + guard_discipline * 0.25 +
                        hip_rotation_score * 0.15 + snap_back_score * 0.15)

        if punch_type not in mechanics_by_type:
            mechanics_by_type[punch_type] = {
                "scores": [],
                "faults": [],
            }

        mechanics_by_type[punch_type]["scores"].append({
            "timestamp": _format_timestamp(fidx, video_fps),
            "extension": round(ext_score * 100),
            "shoulder_engagement": round(sh_score * 100),
            "guard_discipline": round(guard_discipline * 100),
            "hip_rotation": round(hip_rotation_score * 100),
            "snap_back": round(snap_back_score * 100),
            "overall": round(overall_mech * 100),
        })

        # Record faults
        faults = []
        if ext_score < 0.5:
            faults.append(f"Arm not fully extended at {_format_timestamp(fidx, video_fps)}")
        if guard_discipline < 0.4:
            faults.append(f"Guard hand dropped at {_format_timestamp(fidx, video_fps)}")
        if hip_rotation_score < 0.4 and criteria["hip_rotation_expected"] == "significant":
            faults.append(f"Insufficient hip rotation at {_format_timestamp(fidx, video_fps)}")
        if snap_back_score < 0.4:
            faults.append(f"Slow snap-back at {_format_timestamp(fidx, video_fps)}")

        mechanics_by_type[punch_type]["faults"].extend(faults)

    # Aggregate per punch type
    result = {}
    for ptype, data in mechanics_by_type.items():
        scores = data["scores"]
        if not scores:
            continue
        criteria = PUNCH_MECHANICS_CRITERIA.get(ptype, {})
        avg_overall = np.mean([s["overall"] for s in scores])
        result[ptype] = {
            "name": criteria.get("name", ptype.replace("_", " ").title()),
            "count": len(scores),
            "average_score": round(avg_overall, 1),
            "best_score": max(s["overall"] for s in scores),
            "worst_score": min(s["overall"] for s in scores),
            "common_faults": criteria.get("common_faults", []),
            "observed_faults": list(set(data["faults"]))[:5],
            "detail_per_instance": scores[:10],  # Cap at 10 for response size
        }

    return result if result else None


def _range_score(value, low, high):
    """Score how well a value falls within an ideal range (0-1)."""
    if low <= value <= high:
        return 1.0
    if value < low:
        return max(0, 1.0 - (low - value) / 30)
    return max(0, 1.0 - (value - high) / 30)


# -------------------------------------------------------------------
# Guard type detection
# -------------------------------------------------------------------

def _detect_guard_type(guard_scores, frame_angles):
    """Determine which guard type the fighter is predominantly using."""
    if not guard_scores or not frame_angles:
        return "unknown"

    avg_hand_pos = np.mean([g["hand_position"] for g in guard_scores])
    avg_elbow = np.mean([
        (a["left_elbow"] + a["right_elbow"]) / 2 for a in frame_angles
    ])
    avg_knee = np.mean([
        (a["left_knee"] + a["right_knee"]) / 2 for a in frame_angles
    ])
    crouch_level = max(0, 1.0 - avg_knee / 180)

    # Check for asymmetric guard (philly shell indicator)
    left_heights = [a["left_guard_height"] for a in frame_angles]
    right_heights = [a["right_guard_height"] for a in frame_angles]
    avg_left_h = np.mean(left_heights)
    avg_right_h = np.mean(right_heights)
    hand_asymmetry = abs(avg_left_h - avg_right_h)

    # Check if lead arm is extended (L-guard indicator)
    avg_lead_elbow = np.mean([a["left_elbow"] for a in frame_angles])
    lead_extended = avg_lead_elbow > 140

    # Decision tree for guard type
    if lead_extended and avg_hand_pos > 0.3:
        return "l_guard"

    if hand_asymmetry > 0.12 and avg_hand_pos < 0.45:
        return "philly_shell"

    if crouch_level > 0.45 and avg_hand_pos > 0.45 and avg_elbow < 85:
        return "peek_a_boo"

    if avg_hand_pos < 0.3:
        return "low_guard"

    if avg_elbow < 55 and avg_hand_pos > 0.5:
        return "cross_arm"

    if avg_hand_pos > 0.5 and avg_elbow < 110:
        return "high_guard"

    return "high_guard"  # default fallback


# -------------------------------------------------------------------
# Detailed analysis builder
# -------------------------------------------------------------------

def _build_detailed_analysis(overall, stance, guard, guard_type,
                              footwork, head, balance, punches, styles,
                              combinations=None, punch_mechanics=None):
    """Build rich analytical commentary with reasoning chains."""
    sections = {}

    # Overall summary
    interp = get_score_interpretation("overall", overall)
    sections["overall_summary"] = {
        "score": round(overall, 1),
        "interpretation": interp,
    }

    # Guard deep-dive
    sections["guard_analysis"] = {
        "reasoning": build_guard_reasoning(guard, guard_type),
        "guard_type": guard_type,
        "guard_type_name": GUARD_TYPES.get(guard_type, {}).get("name", "Unknown"),
    }

    # Stance deep-dive
    sections["stance_analysis"] = {
        "reasoning": build_stance_reasoning(stance),
    }

    # Footwork
    fw_score = footwork.get("score", 50)
    fw_interp = get_score_interpretation("footwork", fw_score)
    fw_reasoning = [fw_interp] if fw_interp else []

    lateral = footwork.get("lateral_movement", 0)
    width_con = footwork.get("stance_width_consistency", 0)

    if lateral < 20:
        fw_reasoning.append(
            f"**Lateral Movement ({lateral}%):** You're mostly moving forward and back. "
            "Lateral movement creates angles, makes you harder to hit, and opens up the "
            "opponent's guard. Drill: circle the heavy bag — jab while stepping left, "
            "cross while stepping right."
        )
    elif lateral > 60:
        fw_reasoning.append(
            f"**Lateral Movement ({lateral}%):** Strong lateral movement — you're using "
            "angles effectively. Make sure you're not just circling endlessly; "
            "cut angles with purpose, then attack."
        )

    if width_con < 50:
        fw_reasoning.append(
            f"**Stance Width Consistency ({width_con}%):** Your feet are drifting apart "
            "or coming together during movement. Maintain shoulder-width distance between "
            "feet. When you step with one foot, the other follows the same distance. "
            "Never cross your feet."
        )

    sections["footwork_analysis"] = {
        "reasoning": "\n".join(fw_reasoning),
    }

    # Head movement
    hm_score = head.get("score", 50)
    hm_interp = get_score_interpretation("head_movement", hm_score)
    hm_reasoning = [hm_interp] if hm_interp else []

    h_var = head.get("horizontal_variation", 0)
    v_var = head.get("vertical_variation", 0)

    if h_var < 1.0 and v_var < 1.0:
        hm_reasoning.append(
            "Your head stays on the centre line — this makes you predictable and easy to "
            "time. Practice: stand in front of a mirror, throw a jab, then slip your head "
            "to the outside. Every punch should come with a head movement."
        )
    elif h_var > v_var * 2:
        hm_reasoning.append(
            "You're slipping well side-to-side but not incorporating enough vertical "
            "movement (bobs and weaves). Add dipping under hooks and rising into uppercuts "
            "to your defensive repertoire."
        )
    elif v_var > h_var * 2:
        hm_reasoning.append(
            "Good vertical head movement (bobbing/weaving), but add more lateral slips. "
            "Slipping to the outside of straight punches is one of the most effective "
            "defensive techniques in boxing."
        )

    sections["head_movement_analysis"] = {
        "reasoning": "\n".join(hm_reasoning),
    }

    # Balance
    bal_score = balance.get("score", 50)
    bal_interp = get_score_interpretation("balance", bal_score)
    bal_reasoning = [bal_interp] if bal_interp else []

    cog = balance.get("center_of_gravity", 50)
    wd = balance.get("weight_distribution", 50)

    if cog < 50:
        bal_reasoning.append(
            f"**Centre of Gravity ({cog}/100):** You're leaning too far in one direction. "
            "Your shoulders should stay roughly over your hips. When you lean, you lose "
            "power and can be pulled off-balance by a missed punch."
        )
    if wd < 50:
        bal_reasoning.append(
            f"**Weight Distribution ({wd}/100):** Your weight is unevenly distributed "
            "between your legs. Aim for roughly 50/50 in neutral stance, shifting to "
            "60/40 (front leg) when attacking and 60/40 (back leg) when preparing to counter."
        )

    sections["balance_analysis"] = {
        "reasoning": "\n".join(bal_reasoning),
    }

    # Punch analysis (if available)
    if punches:
        punch_reasoning = []
        total_p = punches.get("total_punches", 0)
        total_d = punches.get("total_defensive_moves", 0)
        jab_r = punches.get("jab_ratio", 0)
        variety = punches.get("variety_score", 0)

        if total_p > 0:
            punch_reasoning.append(
                f"**Output:** {total_p} offensive techniques and {total_d} defensive "
                f"movements detected."
            )

        if jab_r < 20 and total_p > 5:
            punch_reasoning.append(
                f"**Jab Usage ({jab_r}%):** Your jab is underutilised. The jab is boxing's "
                "most important weapon — it measures distance, sets up power shots, disrupts "
                "your opponent's timing, and scores points. Aim for at least 30-40% jab ratio."
            )
        elif jab_r > 30:
            punch_reasoning.append(
                f"**Jab Usage ({jab_r}%):** Good jab usage. You're establishing your range "
                "and using the jab as the foundation of your offense."
            )

        if variety < 30:
            punch_reasoning.append(
                f"**Variety ({variety}%):** Limited punch selection. Predictable fighters "
                "are easy to counter. Mix in hooks to the body, uppercuts, and level changes "
                "to keep your opponent guessing."
            )
        elif variety > 60:
            punch_reasoning.append(
                f"**Variety ({variety}%):** Excellent variety in your technique selection. "
                "You're using a well-rounded arsenal."
            )

        if total_d == 0 and total_p > 5:
            punch_reasoning.append(
                "**No defensive movements detected.** Boxing is 'the art of hitting without "
                "being hit.' Incorporate slips, rolls, and blocks between your combinations. "
                "Rule of thumb: throw a combination, then immediately move your head."
            )

        sections["punch_analysis"] = {
            "reasoning": "\n".join(punch_reasoning),
        }

    # Combination analysis
    if combinations:
        combo_reasoning = []
        total_combos = combinations.get("total_combinations", 0)
        flow = combinations.get("flow_score", 0)

        if total_combos > 0:
            combo_reasoning.append(
                f"**{total_combos} combinations detected** with a flow score of {flow}/100."
            )
            for combo in combinations.get("detected_combinations", [])[:5]:
                punches_str = " → ".join(
                    p.replace("_", " ").title() for p in combo["punches"]
                )
                combo_reasoning.append(
                    f"  - **{combo['name']}** at {combo['start_timestamp']}: {punches_str}"
                )
        else:
            combo_reasoning.append(
                "**No combinations detected.** You're throwing single punches. "
                "Combinations are much harder to defend against and score more effectively."
            )

        for rec in combinations.get("recommendations", []):
            combo_reasoning.append(f"\n{rec}")

        sections["combination_analysis"] = {
            "reasoning": "\n".join(combo_reasoning),
        }

    # Punch mechanics
    if punch_mechanics:
        mech_reasoning = []
        for ptype, data in punch_mechanics.items():
            avg = data["average_score"]
            name = data["name"]
            count = data["count"]
            mech_reasoning.append(
                f"**{name}** ({count}x thrown, avg mechanics: {avg}/100):"
            )
            if data["observed_faults"]:
                for fault in data["observed_faults"][:3]:
                    mech_reasoning.append(f"  - {fault}")
            if avg < 50 and data["common_faults"]:
                mech_reasoning.append(f"  Common faults to watch for:")
                for fault in data["common_faults"][:2]:
                    mech_reasoning.append(f"    - {fault}")

        sections["punch_mechanics_analysis"] = {
            "reasoning": "\n".join(mech_reasoning),
        }

    # Style comparison commentary
    if styles:
        top = styles[0]
        style_text = (
            f"Your technique most closely resembles **{top['fighter']}** "
            f"({top['nickname']}) at **{top['similarity']}% similarity**. "
            f"Style: _{top['style']}_.\n\n"
            f"_{top['description']}_\n\n"
        )
        if len(styles) > 1:
            style_text += "Other style matches:\n"
            for s in styles[1:]:
                style_text += f"  - **{s['fighter']}** ({s['nickname']}): {s['similarity']}% — {s['style']}\n"

        sections["style_comparison"] = {
            "reasoning": style_text,
        }

    # Prioritised improvement plan
    sections["improvement_plan"] = {
        "reasoning": build_improvement_plan({
            "guard": guard,
            "footwork": footwork,
            "head_movement": head,
            "balance": balance,
        }),
    }

    return sections


# -------------------------------------------------------------------
# Per-frame evaluators
# -------------------------------------------------------------------

def _evaluate_guard(landmarks, angles):
    """Score guard quality for a single frame (0-1)."""
    left_guard = angles["left_guard_height"]
    right_guard = angles["right_guard_height"]

    left_score = max(0, 1.0 - abs(left_guard) * 3)
    right_score = max(0, 1.0 - abs(right_guard) * 3)

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
    shoulder_center = (landmarks[LEFT_SHOULDER][:2] + landmarks[RIGHT_SHOULDER][:2]) / 2
    hip_center = (landmarks[LEFT_HIP][:2] + landmarks[RIGHT_HIP][:2]) / 2

    offset = np.linalg.norm(shoulder_center - hip_center)
    score = max(0, 1.0 - offset * 5)

    left_knee_y = landmarks[LEFT_KNEE][1]
    right_knee_y = landmarks[RIGHT_KNEE][1]
    knee_diff = abs(left_knee_y - right_knee_y)
    knee_score = max(0, 1.0 - knee_diff * 10)

    return {"center_of_gravity": score, "weight_distribution": knee_score, "overall": (score + knee_score) / 2}


# -------------------------------------------------------------------
# Aggregation functions
# -------------------------------------------------------------------

def _analyze_stance_consistency(stances):
    """Analyze stance consistency across frames."""
    if not stances:
        return {"dominant": "unknown", "consistency": 0}

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
    """Analyze footwork quality."""
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

    if len(foot_positions) > 1:
        deltas = np.diff(foot_positions, axis=0)
        movements = np.linalg.norm(deltas, axis=1)
        lateral_deltas = np.abs(deltas[:, 0])
        total_movement = np.sum(movements)
        lateral_ratio = np.sum(lateral_deltas) / (total_movement + 1e-8)
    else:
        total_movement = 0
        lateral_ratio = 0

    width_std = np.std(stance_widths)
    width_consistency = max(0, 1.0 - width_std * 10)

    movement_score = min(1.0, total_movement * 10)
    score = (width_consistency * 0.4 + movement_score * 0.3 + lateral_ratio * 0.3)

    return {
        "score": round(score * 100, 1),
        "lateral_movement": round(lateral_ratio * 100, 1),
        "stance_width_consistency": round(width_consistency * 100, 1),
        "total_movement": round(total_movement, 4),
    }


def _analyze_head_movement(head_positions):
    """Analyze head movement variation."""
    if len(head_positions) < 2:
        return {"score": 50, "horizontal_variation": 0, "vertical_variation": 0}

    positions = np.array(head_positions)
    x_std = np.std(positions[:, 0])
    y_std = np.std(positions[:, 1])

    variation = (x_std + y_std) / 2
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


def _analyze_punches(move_predictions, video_fps=30.0):
    """Analyze punch distribution and technique from prediction dicts."""
    if not move_predictions:
        return None

    labels = [p["label"] for p in move_predictions]
    counts = Counter(labels)
    total = len(labels)

    punch_types = ["jab", "cross", "lead_hook", "rear_hook", "lead_uppercut", "rear_uppercut"]
    defense_types = ["slip_left", "slip_right", "bob_and_weave", "block"]

    total_punches = sum(counts.get(p, 0) for p in punch_types)
    total_defense = sum(counts.get(d, 0) for d in defense_types)

    distribution = {move: round(counts.get(move, 0) / total * 100, 1) for move in MOVE_LABELS}

    used_types = sum(1 for m in MOVE_LABELS if counts.get(m, 0) > 0)
    variety = used_types / len(MOVE_LABELS)

    jab_ratio = counts.get("jab", 0) / (total_punches + 1e-8)

    return {
        "total_punches": total_punches,
        "total_defensive_moves": total_defense,
        "distribution": distribution,
        "variety_score": round(variety * 100, 1),
        "jab_ratio": round(jab_ratio * 100, 1),
        "punch_defense_ratio": round(total_punches / (total_defense + 1e-8), 2),
    }


# -------------------------------------------------------------------
# Style traits and scoring
# -------------------------------------------------------------------

def _compute_style_traits(guard, footwork, head_movement, balance, punches, frame_angles):
    """Compute normalized style traits for fighter preset matching."""
    traits = {}

    traits["head_movement"] = min(1.0, (head_movement.get("score", 50)) / 100)
    traits["guard_tightness"] = min(1.0, guard.get("score", 50) / 100)
    traits["footwork_lateral"] = min(1.0, footwork.get("lateral_movement", 50) / 100)
    traits["footwork_forward"] = min(1.0, max(0, 1.0 - footwork.get("lateral_movement", 50) / 100))
    traits["distance_control"] = min(1.0, footwork.get("stance_width_consistency", 50) / 100)

    if frame_angles:
        avg_knee = np.mean([
            (a["left_knee"] + a["right_knee"]) / 2 for a in frame_angles
        ])
        traits["crouch_level"] = max(0, 1.0 - avg_knee / 180)
    else:
        traits["crouch_level"] = 0.5

    if punches:
        traits["jab_usage"] = min(1.0, punches.get("jab_ratio", 0) / 100)
        traits["combination_frequency"] = min(1.0, punches.get("variety_score", 0) / 100)
        traits["aggression"] = min(1.0, punches.get("punch_defense_ratio", 1) / 5)
        traits["counter_punching"] = min(1.0, punches.get("total_defensive_moves", 0) / 20)
        traits["body_work"] = 0.5
        traits["punch_power"] = 0.5
        traits["punch_speed"] = 0.5
        traits["ring_cutting"] = traits["footwork_forward"]
    else:
        for k in ["jab_usage", "combination_frequency", "aggression",
                   "counter_punching", "body_work", "punch_power",
                   "punch_speed", "ring_cutting"]:
            traits[k] = 0.5

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
    """Generate strengths and improvement lists."""
    strengths = []
    improvements = []

    # Stance
    if stance.get("consistency", 0) > 80:
        strengths.append(f"Consistent {stance['dominant']} stance ({stance['consistency']}% of frames)")
    elif stance.get("consistency", 0) < 50:
        improvements.append(
            "Work on maintaining a consistent stance — you switch between stances frequently, "
            "which breaks your combination mechanics and balance."
        )

    # Guard
    guard_score = guard.get("score", 0)
    if guard_score > 70:
        strengths.append(f"Strong guard positioning ({guard_score}/100)")
    if guard_score < 50:
        improvements.append(
            "Your guard needs work — keep hands up by your chin with elbows tight to the body."
        )
    if guard.get("guard_drop_rate", 0) > 30:
        improvements.append(
            f"Guard drops in {guard['guard_drop_rate']}% of frames — "
            "focus on returning hands to guard after every punch."
        )
    if guard.get("elbow_tuck", 0) > 75:
        strengths.append("Good elbow tucking — body well protected")

    # Footwork
    footwork_score = footwork.get("score", 0)
    if footwork_score > 70:
        strengths.append(f"Good purposeful footwork ({footwork_score}/100)")
    if footwork.get("lateral_movement", 0) > 40:
        strengths.append("Strong lateral movement — hard to hit")
    if footwork.get("lateral_movement", 0) < 15:
        improvements.append("Add lateral movement — side-to-side movement creates angles and makes you harder to hit.")
    if footwork.get("stance_width_consistency", 0) < 50:
        improvements.append("Maintain consistent stance width — inconsistent foot spacing hurts balance and power.")

    # Head movement
    head_score = head_movement.get("score", 0)
    if head_score > 70:
        strengths.append(f"Active head movement ({head_score}/100)")
    if head_score < 30:
        improvements.append("Your head is too stationary — practice slipping, bobbing, and weaving.")

    # Balance
    balance_score = balance.get("score", 0)
    if balance_score > 75:
        strengths.append(f"Excellent balance ({balance_score}/100)")
    if balance_score < 45:
        improvements.append("Work on balance — keep weight centered with knees slightly bent.")

    # Punches
    if punches:
        if punches.get("variety_score", 0) > 60:
            strengths.append("Good punch variety — well-rounded arsenal")
        if punches.get("variety_score", 0) < 30:
            improvements.append("Diversify your punch selection — mix in hooks, uppercuts, and body shots.")
        if punches.get("jab_ratio", 0) > 30:
            strengths.append(f"Good jab usage ({punches['jab_ratio']}%)")
        elif punches.get("jab_ratio", 0) < 15 and punches.get("total_punches", 0) > 5:
            improvements.append("Use your jab more — it's the most important punch in boxing.")
        if punches.get("total_defensive_moves", 0) < 3 and punches.get("total_punches", 0) > 10:
            improvements.append("Incorporate more defensive movements between combinations.")

    if not strengths:
        strengths.append("Keep training — every session builds your foundation.")
    if not improvements:
        improvements.append("Looking solid overall — continue refining technique and speed.")

    return strengths, improvements
