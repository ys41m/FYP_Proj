"""
Boxing fundamentals knowledge base.

Encodes expert knowledge about stances, guards, techniques, and their
trade-offs. Used by the analyzer to generate targeted, analytical feedback.
"""

# ---------------------------------------------------------------------------
# Stances
# ---------------------------------------------------------------------------

STANCES = {
    "orthodox": {
        "name": "Orthodox",
        "description": "Left foot and left hand forward, right hand rear. The most common stance, natural for right-handed fighters.",
        "strengths": [
            "Strong rear-hand cross (power hand at the back)",
            "Natural for ~90% of fighters — more training partners available",
            "Good liver protection (right side shielded by rear elbow)",
            "Well-documented combinations and techniques to learn from",
        ],
        "weaknesses": [
            "Liver exposed to opponent's left hooks from the open side",
            "Predictable lead hand (jab) angle against orthodox opponents",
            "Right foot positioned rear limits right-kick threat in MMA crossover",
        ],
        "ideal_for": "Right-handed fighters, beginners, those seeking a strong foundational stance.",
    },
    "southpaw": {
        "name": "Southpaw",
        "description": "Right foot and right hand forward, left hand rear. Favoured by left-handed fighters and those seeking an angular advantage.",
        "strengths": [
            "Unfamiliar angles — most opponents train against orthodox",
            "Dominant-hand cross lands from a blind angle vs orthodox fighters",
            "Lead right hand can exploit the open side of orthodox opponents",
            "Rear left hook / left straight can be devastating power shots",
        ],
        "weaknesses": [
            "Fewer southpaw training partners to spar with",
            "Liver exposed to opponent's right hooks (open side)",
            "Many coaches teach orthodox-centric combinations — adaptation needed",
        ],
        "ideal_for": "Left-handed fighters, or orthodox fighters developing a switch style for unpredictability.",
    },
    "square": {
        "name": "Square / Neutral",
        "description": "Feet roughly even, neither foot clearly leading. Often seen in beginners or fighters transitioning between stances.",
        "strengths": [
            "Equal power generation from both hands",
            "Quick pivot to either orthodox or southpaw",
            "Balanced weight distribution for quick retreats",
        ],
        "weaknesses": [
            "Larger target profile — chest is fully exposed",
            "Poor lateral movement — harder to angle off",
            "Less mechanical advantage for generating power on crosses",
            "Unstable base — easier to push off balance",
        ],
        "ideal_for": "Only momentary use during stance switches. Not recommended as a primary stance.",
    },
}

# ---------------------------------------------------------------------------
# Guard types — detection criteria and analysis
# ---------------------------------------------------------------------------

GUARD_TYPES = {
    "high_guard": {
        "name": "High Guard (Classic)",
        "description": "Both hands up by the temples/forehead, elbows tight to the body. The foundational guard taught to all beginners.",
        "detection": {
            "hand_height": (0.6, 1.0),       # wrist at or above nose level (score)
            "elbow_angle": (30, 100),          # degrees
            "crouch_level": (0.0, 0.4),        # low crouch
            "lead_hand_extended": False,
        },
        "strengths": [
            "Excellent facial protection from straight punches and hooks",
            "Easy to learn — good for beginners building fundamentals",
            "Facilitates quick parries and catches",
            "Protects against headshots from any angle when elbows are tight",
        ],
        "weaknesses": [
            "Limited peripheral vision with hands high",
            "Body is exposed — vulnerable to body shots and uppercuts",
            "Can become energy-draining if held for long rounds",
            "Slower transition to offense compared to some other guards",
        ],
        "best_used_by": "Beginners, pressure fighters, fighters with weaker head movement.",
        "famous_users": ["Marco Antonio Barrera", "Winky Wright"],
    },
    "peek_a_boo": {
        "name": "Peek-a-Boo",
        "description": "Hands by the cheeks, forearms covering the face, combined with a deep crouch and constant head movement. Popularised by Cus D'Amato and Mike Tyson.",
        "detection": {
            "hand_height": (0.5, 0.9),
            "elbow_angle": (25, 80),
            "crouch_level": (0.5, 1.0),         # significant crouch
            "lead_hand_extended": False,
        },
        "strengths": [
            "Exceptional head protection with forearms acting as a shield",
            "Deep crouch makes you a smaller target and loads power into hooks and uppercuts",
            "Facilitates explosive in-fighting — power shots from the crouch",
            "Constant head movement makes you very hard to hit cleanly",
        ],
        "weaknesses": [
            "Requires elite conditioning — crouching and bobbing is exhausting",
            "Limited reach utilisation — have to close distance to land",
            "Vulnerable to uppercuts if the crouch is too deep",
            "Difficult to master — timing and rhythm take years to develop",
        ],
        "best_used_by": "Inside fighters, short/stocky fighters, those with explosive power.",
        "famous_users": ["Mike Tyson", "Floyd Patterson", "Jose Torres"],
    },
    "philly_shell": {
        "name": "Philly Shell / Shoulder Roll",
        "description": "Lead hand held low across the midsection, rear hand up by the cheek, lead shoulder raised to deflect incoming punches. Also called the Shoulder Roll.",
        "detection": {
            "hand_height": (0.0, 0.4),         # lead hand low
            "elbow_angle": (80, 160),            # arms less tucked
            "crouch_level": (0.0, 0.3),
            "lead_hand_extended": False,
            "asymmetric_hands": True,            # one high, one low
        },
        "strengths": [
            "Excellent at deflecting straight punches (jabs and crosses roll off the shoulder)",
            "Sets up devastating counter-punches — deflect then counter in one motion",
            "Energy-efficient — uses angles rather than blocking with force",
            "Keeps rear hand loaded and ready for counter right hands",
        ],
        "weaknesses": [
            "Vulnerable to hooks from the lead side (comes around the shoulder)",
            "Body exposed on the lead side with hand dropped low",
            "Requires elite timing and reflexes — not for beginners",
            "Struggles against southpaw opponents (angles are reversed)",
        ],
        "best_used_by": "Counter-punchers with elite timing. Experienced fighters only.",
        "famous_users": ["Floyd Mayweather Jr.", "James Toney", "Pernell Whitaker"],
    },
    "low_guard": {
        "name": "Low Guard",
        "description": "Hands held at or below chin level, relying on reflexes, footwork, and distance management rather than a physical barrier.",
        "detection": {
            "hand_height": (0.0, 0.35),
            "elbow_angle": (90, 180),
            "crouch_level": (0.0, 0.3),
            "lead_hand_extended": False,
        },
        "strengths": [
            "Better vision and awareness of incoming punches",
            "Faster punches — less distance for hands to travel",
            "Psychological intimidation — shows confidence",
            "Can bait opponents into overcommitting",
        ],
        "weaknesses": [
            "Head is exposed — requires elite reflexes to avoid clean shots",
            "Very risky for beginners without developed timing",
            "One mistake can lead to a knockdown or knockout",
            "Ineffective against fast combination punchers",
        ],
        "best_used_by": "Elite-level fighters with exceptional reflexes and footwork.",
        "famous_users": ["Muhammad Ali", "Prince Naseem Hamed", "Roy Jones Jr."],
    },
    "l_guard": {
        "name": "L-Guard / Extended Guard",
        "description": "Lead hand extended forward (framing), rear hand by the cheek. Creates distance and controls range with the lead hand.",
        "detection": {
            "hand_height": (0.3, 0.7),
            "elbow_angle": (130, 180),           # lead arm quite extended
            "crouch_level": (0.0, 0.4),
            "lead_hand_extended": True,
        },
        "strengths": [
            "Excellent range control — lead hand acts as a measuring tool",
            "Disrupts opponent's rhythm by framing and posting",
            "Sets up angles and lateral movement from the extended position",
            "Can transition smoothly into jabs from the extended position",
        ],
        "weaknesses": [
            "Lead side exposed — extended arm can be parried to open a line of attack",
            "Requires constant footwork to maintain ideal distance",
            "Less protection against inside fighting if opponent closes distance",
            "Lead arm can fatigue from being held extended",
        ],
        "best_used_by": "Technical fighters, tall fighters with reach advantage, out-fighters.",
        "famous_users": ["Vasyl Lomachenko", "Guillermo Rigondeaux", "Terence Crawford"],
    },
    "cross_arm": {
        "name": "Cross-Arm Guard",
        "description": "Arms crossed in front of the face and body, creating a layered barrier. A primarily defensive shell.",
        "detection": {
            "hand_height": (0.5, 0.9),
            "elbow_angle": (20, 60),             # very tight
            "crouch_level": (0.0, 0.5),
            "lead_hand_extended": False,
        },
        "strengths": [
            "Maximum facial and upper body protection",
            "Absorbs heavy shots effectively — good for weathering storms",
            "Can be combined with head movement for added defense",
        ],
        "weaknesses": [
            "Very limited offensive capability while holding the guard",
            "Slow transition to punching — telegraphs when you open up",
            "Body and sides still vulnerable to hooks and uppercuts",
            "Can lead to passive fighting if overused",
        ],
        "best_used_by": "Fighters under heavy fire needing to survive rounds. Situational guard only.",
        "famous_users": ["Archie Moore", "George Foreman"],
    },
}

# ---------------------------------------------------------------------------
# Technique analysis templates — chains of reasoning for feedback
# ---------------------------------------------------------------------------

GUARD_FEEDBACK = {
    "high_guard": {
        "good": "You're maintaining a solid high guard — hands are up protecting the face, elbows tucked. This is a strong defensive foundation.",
        "advice": "With a high guard, focus on keeping your elbows tight to protect the body. Practice quick parries rather than just absorbing shots. Add subtle head movement behind the guard to avoid taking clean shots even when blocking.",
    },
    "peek_a_boo": {
        "good": "You're showing peek-a-boo characteristics — crouched stance with hands framing the face. This is an aggressive, protection-heavy guard.",
        "advice": "Make sure to combine the crouch with constant head movement (side to side). Avoid staying static in the crouch — a stationary peek-a-boo is vulnerable to uppercuts. Practice exploding out of the crouch into hooks and combinations.",
    },
    "philly_shell": {
        "good": "You're using a Philly Shell / shoulder roll position — lead shoulder up, hands positioned for rolling punches.",
        "advice": "The shoulder roll is high-risk/high-reward. Make sure your lead shoulder is truly raised to deflect jabs. Keep your rear hand glued to your cheek. Drill the catch-and-counter rhythm: roll → counter right hand. Watch for hooks coming around the shoulder — that's your blind spot.",
    },
    "low_guard": {
        "good": "You're fighting with a low guard — this gives you speed and vision advantages.",
        "advice": "A low guard relies entirely on reflexes and footwork. Make sure you're using distance management — don't stand in range with hands down. Use the low hand position to generate speed on counters, but be ready to shell up when pressured. This guard is only safe at range.",
    },
    "l_guard": {
        "good": "You're using an L-Guard / extended lead — this is great for controlling distance and setting up your jab.",
        "advice": "Keep the lead hand active — post, frame, and measure your opponent. Don't let it become a static arm. Your rear hand must stay glued to your chin. Use lateral movement to complement the extended guard — circling keeps you safe from opponents who try to crash inside your lead hand.",
    },
    "cross_arm": {
        "good": "You're using a cross-arm guard — this offers strong frontal protection when under fire.",
        "advice": "This guard should be situational, not your default. Use it to weather storms, then transition to a more offensive guard when the pressure eases. Practice opening up quickly to counter between your opponent's combinations.",
    },
    "unknown": {
        "good": "Your guard shows some protective positioning.",
        "advice": "Work on establishing a consistent guard style. Start with a high guard as your foundation — hands up by the temples, elbows tight. Once that becomes second nature, you can explore other guard types like the peek-a-boo or philly shell.",
    },
}

STANCE_FEEDBACK = {
    "orthodox": {
        "consistent": "Strong orthodox stance consistency — this means your combinations flow naturally and your weight transfer is predictable (in a good way). Your jab and cross have a solid mechanical foundation.",
        "inconsistent": "Your orthodox stance is drifting — you're frequently shifting to a square or southpaw position without intent. This breaks your combination mechanics and leaves you off-balance. Drill footwork patterns: step-jab, pivot, reset to stance.",
    },
    "southpaw": {
        "consistent": "Solid southpaw consistency — you're holding your right-foot-forward position well. This gives you angular advantages that most orthodox opponents aren't used to.",
        "inconsistent": "Your southpaw stance isn't stable — you're drifting to square or switching unintentionally. This negates the angular advantage southpaws have. Practice holding position after throwing combinations.",
    },
    "square": {
        "consistent": "You're spending significant time in a square stance. While this can be intentional during stance switches, as a primary position it exposes your center line and limits your power generation.",
        "inconsistent": "Your stance is highly variable with a lot of time spent square. This suggests you haven't committed to a dominant stance yet. Pick orthodox or southpaw as your base and drill it until it's automatic.",
    },
}

# ---------------------------------------------------------------------------
# Score interpretation and improvement chains
# ---------------------------------------------------------------------------

SCORE_INTERPRETATIONS = {
    "overall": {
        (0, 30): "Significant room for improvement across fundamentals. Focus on the basics — stance, guard, and simple combinations.",
        (30, 50): "Developing fighter. Some fundamentals are there but inconsistent. Focus on making your guard and stance automatic before adding complexity.",
        (50, 65): "Decent fundamentals with clear areas to sharpen. You have a foundation — now refine specific weaknesses identified below.",
        (65, 80): "Good technical base. Your fundamentals are solid — focus on the specific refinements below to reach elite level.",
        (80, 90): "Strong technical fighter. Most fundamentals are well-developed. Fine-tune the small details below.",
        (90, 100): "Elite-level technique. Your fundamentals are exceptional — focus on tactical adjustments and specific fight preparations.",
    },
    "guard": {
        (0, 30): "Your guard needs serious work — hands are dropping and leaving your head exposed. This is the #1 priority to fix.",
        (30, 50): "Guard is inconsistent — it's there sometimes but drops during activity. Drill shadow boxing while consciously resetting your guard after every punch.",
        (50, 70): "Decent guard but with gaps. Focus on the specific issues identified — whether it's hand height, elbow tuck, or consistency.",
        (70, 85): "Good guard discipline. You're protecting yourself well — refine the details like guard recovery speed.",
        (85, 100): "Excellent guard. Your hands stay in position and recover quickly. This is a real strength.",
    },
    "footwork": {
        (0, 30): "Footwork is a major weakness — you're flat-footed and stationary. Start with basic lateral movement drills.",
        (30, 50): "Footwork is developing but limited. You're moving but without purpose. Drill: step-jab-step, pivot drills, circle drills.",
        (50, 70): "Adequate footwork with room to grow. You're moving but could be more deliberate. Focus on cutting angles rather than just circling.",
        (70, 85): "Good footwork. You're using lateral movement well — add in level changes and angle-offs to make it elite.",
        (85, 100): "Excellent footwork. You're light on your feet and using movement effectively. Strong foundation for your style.",
    },
    "head_movement": {
        (0, 30): "Your head is very stationary — this makes you an easy target. Start with simple slip drills (slip bag or partner feints).",
        (30, 50): "Some head movement but not enough. You need to move your head off the centre line more frequently — especially between and during combinations.",
        (50, 70): "Decent head movement. You're moving off-line but could be more varied. Mix slips, rolls, and pull-backs.",
        (70, 85): "Good head movement. You're difficult to hit cleanly — keep developing the rhythm and timing.",
        (85, 100): "Excellent head movement. This is a real defensive weapon — your opponent will struggle to land clean.",
    },
    "balance": {
        (0, 30): "Your balance is a major concern — weight distribution is uneven and centre of gravity is off. Focus on stance fundamentals.",
        (30, 50): "Balance is shaky — you're leaning or overextending on punches. Drill: throw punches slowly, focusing on staying centered.",
        (50, 70): "Decent balance with some lapses. You maintain position most of the time but lose it under pressure or when combination punching.",
        (70, 85): "Good balance. Your weight stays centered for the most part — refine it during combination work.",
        (85, 100): "Excellent balance. You stay centered and grounded even during complex sequences. Strong foundation.",
    },
}

# ---------------------------------------------------------------------------
# Improvement reasoning — connects observations to advice
# ---------------------------------------------------------------------------

def build_guard_reasoning(guard_data, guard_type):
    """Build a chain of reasoning about guard performance."""
    chains = []
    info = GUARD_TYPES.get(guard_type, GUARD_TYPES["high_guard"])
    feedback = GUARD_FEEDBACK.get(guard_type, GUARD_FEEDBACK["unknown"])

    score = guard_data.get("score", 0)

    # What we observed
    chains.append(f"**Guard Type Detected: {info['name']}**")
    chains.append(f"_{info['description']}_")

    if score >= 65:
        chains.append(feedback["good"])
    else:
        chains.append(f"Your guard score is {score}/100 — there's meaningful room to improve.")

    # Specific observations
    hand_pos = guard_data.get("hand_position", 0)
    elbow_tuck = guard_data.get("elbow_tuck", 0)
    drop_rate = guard_data.get("guard_drop_rate", 0)

    if hand_pos < 50:
        chains.append(f"**Hand Height ({hand_pos}/100):** Your hands are dropping below your chin line. "
                      "This leaves your head exposed to straight punches (jabs and crosses). "
                      "Drill: shadow box for 3-minute rounds with the sole focus of keeping hands at temple height. "
                      "Reset your guard after every single punch.")

    if elbow_tuck < 50:
        chains.append(f"**Elbow Tuck ({elbow_tuck}/100):** Your elbows are flaring out, leaving gaps in your guard. "
                      "Hooks and body shots can slip through wide elbows. "
                      "Drill: hold a tennis ball under each armpit while shadow boxing — if it drops, your elbows are flaring.")

    if drop_rate > 30:
        chains.append(f"**Guard Drop Rate ({drop_rate:.0f}%):** You're dropping your guard in {drop_rate:.0f}% of frames. "
                      "This is a dangerous habit — especially after throwing punches. "
                      "Every punch should return to guard position before the next action.")

    chains.append(feedback["advice"])

    # Guard type specific strengths/weaknesses
    chains.append(f"\n**Strengths of the {info['name']}:**")
    for s in info["strengths"][:3]:
        chains.append(f"  - {s}")
    chains.append(f"**Watch out for:**")
    for w in info["weaknesses"][:3]:
        chains.append(f"  - {w}")

    return "\n".join(chains)


def build_stance_reasoning(stance_data):
    """Build a chain of reasoning about stance performance."""
    chains = []
    dominant = stance_data.get("dominant", "orthodox")
    consistency = stance_data.get("consistency", 0)
    breakdown = stance_data.get("breakdown", {})
    info = STANCES.get(dominant, STANCES["orthodox"])
    feedback = STANCE_FEEDBACK.get(dominant, STANCE_FEEDBACK["orthodox"])

    chains.append(f"**Dominant Stance: {info['name']}**")
    chains.append(f"_{info['description']}_")

    if consistency >= 75:
        chains.append(feedback["consistent"])
    else:
        chains.append(feedback["inconsistent"])

    chains.append(f"Stance consistency: {consistency:.0f}%")

    if breakdown:
        chains.append("Stance breakdown across the video:")
        for stance_name, pct in breakdown.items():
            chains.append(f"  - {stance_name.title()}: {pct:.0f}%")

    chains.append(f"\n**Strengths of {info['name']}:**")
    for s in info["strengths"][:3]:
        chains.append(f"  - {s}")
    chains.append(f"**Weaknesses to be aware of:**")
    for w in info["weaknesses"][:2]:
        chains.append(f"  - {w}")

    return "\n".join(chains)


def get_score_interpretation(category, score):
    """Return the interpretation text for a score in a category."""
    ranges = SCORE_INTERPRETATIONS.get(category, {})
    for (low, high), text in ranges.items():
        if low <= score < high:
            return text
    return ""


def build_improvement_plan(analysis):
    """Build a prioritised improvement plan from the full analysis."""
    priorities = []

    guard_score = analysis.get("guard", {}).get("score", 50)
    footwork_score = analysis.get("footwork", {}).get("score", 50)
    head_score = analysis.get("head_movement", {}).get("score", 50)
    balance_score = analysis.get("balance", {}).get("score", 50)

    components = [
        ("guard", guard_score, "Guard"),
        ("footwork", footwork_score, "Footwork"),
        ("head_movement", head_score, "Head Movement"),
        ("balance", balance_score, "Balance"),
    ]

    # Sort by score ascending (worst first)
    components.sort(key=lambda x: x[1])

    priorities.append("**Improvement Priority Order** (weakest areas first):\n")

    for i, (key, score, label) in enumerate(components, 1):
        interp = get_score_interpretation(key, score)
        priorities.append(f"**{i}. {label} ({score}/100)**")
        if interp:
            priorities.append(f"   {interp}")
        # Add drill recommendations for weakest areas
        if score < 60:
            drills = get_drills_for_weakness(key)
            if drills:
                priorities.append(f"   **Recommended Drills:**")
                for drill in drills[:2]:
                    priorities.append(f"   - {drill['name']}: {drill['description']} ({drill['prescription']})")
        priorities.append("")

    return "\n".join(priorities)


# ---------------------------------------------------------------------------
# Combination patterns — common boxing combinations and their purposes
# ---------------------------------------------------------------------------

COMBINATION_PATTERNS = {
    "jab_cross": {
        "name": "1-2 (Jab-Cross)",
        "sequence": ["jab", "cross"],
        "description": "The most fundamental combination in boxing. The jab measures distance and sets up the power cross.",
        "when_to_use": "Opening offense, establishing range, testing opponent's defense.",
        "follow_ups": ["lead_hook", "slip_right"],
    },
    "jab_jab_cross": {
        "name": "1-1-2 (Double Jab-Cross)",
        "sequence": ["jab", "jab", "cross"],
        "description": "Double jab disrupts timing and creates openings for the cross. The second jab often lands.",
        "when_to_use": "Against aggressive opponents who slip the first jab, or to establish jab dominance.",
        "follow_ups": ["lead_hook", "bob_and_weave"],
    },
    "jab_cross_hook": {
        "name": "1-2-3 (Jab-Cross-Hook)",
        "sequence": ["jab", "cross", "lead_hook"],
        "description": "Classic three-punch combination. The hook catches opponents focused on the straight punches.",
        "when_to_use": "When opponent guards against straight punches, exposing the side of their head.",
        "follow_ups": ["cross", "slip_left"],
    },
    "jab_cross_hook_cross": {
        "name": "1-2-3-2 (Jab-Cross-Hook-Cross)",
        "sequence": ["jab", "cross", "lead_hook", "cross"],
        "description": "Four-punch combination with alternating power. The final cross is often unexpected.",
        "when_to_use": "When you have an opponent on the ropes or when they're retreating.",
        "follow_ups": ["lead_uppercut", "block"],
    },
    "jab_lead_hook": {
        "name": "1-3 (Jab-Hook)",
        "sequence": ["jab", "lead_hook"],
        "description": "Quick change of angle from straight to curved. Catches opponents who over-commit to parrying the jab.",
        "when_to_use": "Against parry-heavy defenders or when fighting at mid-range.",
        "follow_ups": ["cross", "rear_uppercut"],
    },
    "cross_lead_hook_cross": {
        "name": "2-3-2 (Cross-Hook-Cross)",
        "sequence": ["cross", "lead_hook", "cross"],
        "description": "Power-heavy combination. Risky opening with the cross but devastating if it lands.",
        "when_to_use": "Counter-attacking off a slip, or when opponent drops their guard.",
        "follow_ups": ["lead_hook", "slip_left"],
    },
    "jab_rear_uppercut_lead_hook": {
        "name": "1-6-3 (Jab-Uppercut-Hook)",
        "sequence": ["jab", "rear_uppercut", "lead_hook"],
        "description": "Level-changing combination. Jab high, uppercut through the middle, hook around the guard.",
        "when_to_use": "Against tall opponents or those with a tight high guard.",
        "follow_ups": ["cross", "bob_and_weave"],
    },
    "lead_hook_cross_lead_hook": {
        "name": "3-2-3 (Hook-Cross-Hook)",
        "sequence": ["lead_hook", "cross", "lead_hook"],
        "description": "Triangle combination. The second hook catches opponents adjusting to the angle change.",
        "when_to_use": "At mid-range, especially against fighters who shell up after the first hook.",
        "follow_ups": ["rear_uppercut", "slip_right"],
    },
}


# ---------------------------------------------------------------------------
# Drill recommendations — mapped by weakness type
# ---------------------------------------------------------------------------

DRILL_RECOMMENDATIONS = {
    "guard": [
        {
            "name": "Tennis Ball Guard Drill",
            "description": "Hold a tennis ball under each armpit while shadow boxing. Forces elbows to stay tucked.",
            "prescription": "3 rounds x 3 min, rest 1 min between rounds",
        },
        {
            "name": "Wall Guard Reset",
            "description": "Stand arm's length from a wall. Throw 1-2 combos then touch the wall with both gloves at chin height. Builds guard return habit.",
            "prescription": "3 rounds x 2 min, 50 reps per round",
        },
        {
            "name": "Mirror Shadow Boxing (Guard Focus)",
            "description": "Shadow box in front of a mirror with sole focus on returning hands to guard after every punch.",
            "prescription": "5 rounds x 3 min, mentally score yourself on guard discipline",
        },
        {
            "name": "Partner Touch Drill",
            "description": "Partner tries to touch your chin with open hand while you keep guard up. Develops guard awareness under pressure.",
            "prescription": "3 rounds x 2 min each person",
        },
    ],
    "footwork": [
        {
            "name": "Ladder Drills",
            "description": "Agility ladder work: in-out, lateral shuffle, Ali shuffle. Develops foot speed and coordination.",
            "prescription": "4 sets x 4 patterns, 30 seconds rest between sets",
        },
        {
            "name": "Circle the Bag",
            "description": "Circle the heavy bag in both directions, jabbing as you move. Never stop your feet.",
            "prescription": "3 rounds x 3 min per direction",
        },
        {
            "name": "Cone Pivot Drill",
            "description": "Place 4 cones in a square. Move between cones with proper boxing footwork — never cross your feet.",
            "prescription": "4 rounds x 2 min, alternate clockwise and counter-clockwise",
        },
        {
            "name": "Shadow Boxing with Line",
            "description": "Shadow box along a straight line on the floor. Practice lateral cuts and angle-offs while maintaining stance width.",
            "prescription": "3 rounds x 3 min",
        },
    ],
    "head_movement": [
        {
            "name": "Slip Line Drill",
            "description": "Run a rope at chin height between two poles. Practice slipping under it from both sides.",
            "prescription": "5 rounds x 2 min, alternate slip direction each round",
        },
        {
            "name": "Pendulum Head Movement",
            "description": "Stand in stance and sway head side-to-side like a pendulum. Add bobs (down-and-under) every 3rd sway.",
            "prescription": "3 rounds x 3 min, match to breathing rhythm",
        },
        {
            "name": "Partner Feint Drill",
            "description": "Partner throws slow jabs and hooks. You slip, bob, or weave each one. Builds reactive head movement.",
            "prescription": "4 rounds x 2 min, increase speed gradually",
        },
        {
            "name": "Double-End Bag Rhythm",
            "description": "Work the double-end bag with focus on slipping the bag's return. Jab, slip, jab, slip rhythm.",
            "prescription": "4 rounds x 3 min",
        },
    ],
    "balance": [
        {
            "name": "Single-Leg Stance Punching",
            "description": "Stand on one leg in front of a mirror and throw slow punches. Develops core stability and balance under action.",
            "prescription": "3 rounds x 1 min per leg",
        },
        {
            "name": "Slow-Motion Combination Drill",
            "description": "Throw full combinations at 25% speed, focusing on staying centered over your base.",
            "prescription": "3 rounds x 3 min",
        },
        {
            "name": "Balance Board Shadow Boxing",
            "description": "Shadow box while standing on a balance board or BOSU ball. Forces core engagement.",
            "prescription": "3 rounds x 2 min, start with simple jabs before adding combos",
        },
    ],
    "punch_mechanics": [
        {
            "name": "Heavy Bag Power Rotation Drill",
            "description": "Throw single punches on the heavy bag with maximum hip rotation. Feel the power chain from feet through hips to fist.",
            "prescription": "3 rounds x 20 punches per type (jab, cross, hook)",
        },
        {
            "name": "Snap-Back Mirror Drill",
            "description": "Throw punches at a mirror and focus on bringing the hand back to guard faster than it went out.",
            "prescription": "3 rounds x 3 min, count how many clean snap-backs per round",
        },
        {
            "name": "Towel Whip Drill",
            "description": "Hold a small towel in each hand and throw punches making the towel snap. Develops wrist speed and snap.",
            "prescription": "3 rounds x 2 min",
        },
    ],
    "combinations": [
        {
            "name": "Number Calling Drill",
            "description": "Partner calls out numbers (1=jab, 2=cross, 3=hook, etc.) and you throw the corresponding combination.",
            "prescription": "3 rounds x 3 min, partner varies tempo",
        },
        {
            "name": "Combination Flow on Heavy Bag",
            "description": "Work pre-set combinations on the heavy bag: 1-2, 1-2-3, 1-2-3-2, 1-6-3. Flow between them without stopping.",
            "prescription": "4 rounds x 3 min, focus on flow not power",
        },
        {
            "name": "Mitt Work (Combination Focus)",
            "description": "Work with a partner holding mitts. Throw called combinations with emphasis on smooth transitions between punches.",
            "prescription": "5 rounds x 3 min",
        },
    ],
}


def get_drills_for_weakness(weakness_key):
    """Get drill recommendations for a specific weakness area."""
    return DRILL_RECOMMENDATIONS.get(weakness_key, [])


# ---------------------------------------------------------------------------
# Counter opportunities — opponent habit -> recommended counter
# ---------------------------------------------------------------------------

COUNTER_OPPORTUNITIES = {
    "drops_guard_after_cross": {
        "habit": "Drops guard after throwing a cross",
        "counter": "Counter with a lead hook as their right hand drops after the cross.",
        "drill": "Have partner throw a cross, immediately counter with 3 (lead hook). Repeat until automatic.",
    },
    "drops_guard_after_jab": {
        "habit": "Drops lead hand after jabbing",
        "counter": "Slip outside the jab and counter with a straight right (cross) over the top.",
        "drill": "Partner jabs, you slip right and counter with 2 (cross). Focus on timing, not power.",
    },
    "lunges_forward": {
        "habit": "Lunges forward when attacking",
        "counter": "Pivot off-angle and counter with a hook as they overcommit forward.",
        "drill": "As partner steps in, pivot 45 degrees and throw a 3 (lead hook) to catch them coming in.",
    },
    "telegraphs_hooks": {
        "habit": "Winds up / telegraphs hooks",
        "counter": "Step inside the hook and throw a short uppercut or straight punch.",
        "drill": "When you see the wind-up, step forward with a 6 (rear uppercut) inside their arc.",
    },
    "static_head": {
        "habit": "Keeps head stationary / on centre line",
        "counter": "Feint to draw a reaction, then throw straight punches to their static head.",
        "drill": "Feint jab, then immediately throw a real 1-2 (jab-cross) to the same target.",
    },
    "low_guard_habit": {
        "habit": "Consistently fights with a low guard",
        "counter": "Attack with straight punches to the head. Double jab-cross is highly effective.",
        "drill": "Open with 1-1-2 (double jab-cross) whenever you see the guard drop below chin level.",
    },
    "retreats_straight_back": {
        "habit": "Retreats in a straight line when pressured",
        "counter": "Cut off the ring by stepping to the side they retreat toward. Corner them.",
        "drill": "When opponent steps back, step diagonally to cut the angle. Then attack with 1-2-3.",
    },
    "drops_guard_between_combos": {
        "habit": "Drops guard between their own combinations",
        "counter": "Time your counter to land in the gap between their combinations.",
        "drill": "As opponent finishes their combo and pauses, immediately fire your own 1-2 or 2-3.",
    },
}


# ---------------------------------------------------------------------------
# Punch mechanics criteria — ideal angle ranges for each punch type
# ---------------------------------------------------------------------------

PUNCH_MECHANICS_CRITERIA = {
    "jab": {
        "name": "Jab",
        "ideal_elbow_extension": (155, 180),  # near full extension
        "ideal_shoulder_angle": (70, 110),     # arm raised to shoulder level
        "hip_rotation_expected": "minimal",    # jab is arm-dominant
        "rear_hand_position": "chin",          # rear hand stays at chin
        "snap_back_priority": "high",          # quick return to guard
        "common_faults": [
            "Dropping the rear hand while jabbing",
            "Pushing the jab instead of snapping it",
            "Leaning forward and over-extending",
            "Not rotating the fist on impact",
        ],
    },
    "cross": {
        "name": "Cross / Straight Right",
        "ideal_elbow_extension": (160, 180),   # full extension
        "ideal_shoulder_angle": (80, 120),      # shoulder drives through
        "hip_rotation_expected": "significant", # power comes from hip rotation
        "rear_hand_position": "n/a",            # this IS the rear hand
        "snap_back_priority": "high",
        "common_faults": [
            "No hip rotation — arm-punching reduces power by ~40%",
            "Dropping the lead hand while throwing the cross",
            "Stepping too wide — losing stance integrity",
            "Telegraphing by pulling the hand back before throwing",
        ],
    },
    "lead_hook": {
        "name": "Lead Hook",
        "ideal_elbow_extension": (75, 110),    # arm bent at ~90 degrees
        "ideal_shoulder_angle": (70, 100),      # arm at shoulder level
        "hip_rotation_expected": "significant", # torso rotation drives the hook
        "rear_hand_position": "chin",
        "snap_back_priority": "medium",
        "common_faults": [
            "Winding up — pulling the arm back telegraphs the hook",
            "Elbow dropping below the fist — loses horizontal force",
            "No hip rotation — hook becomes an arm swing",
            "Head stays on centre line — should move off-line with the hook",
        ],
    },
    "rear_hook": {
        "name": "Rear Hook",
        "ideal_elbow_extension": (75, 110),
        "ideal_shoulder_angle": (70, 100),
        "hip_rotation_expected": "significant",
        "rear_hand_position": "n/a",
        "snap_back_priority": "medium",
        "common_faults": [
            "Over-rotating and losing balance",
            "Dropping the lead hand during the rotation",
            "Throwing from too far away — hooks are mid-range punches",
        ],
    },
    "lead_uppercut": {
        "name": "Lead Uppercut",
        "ideal_elbow_extension": (60, 100),    # tight bend
        "ideal_shoulder_angle": (40, 80),       # arm below shoulder level
        "hip_rotation_expected": "moderate",    # dip and drive up
        "rear_hand_position": "chin",
        "snap_back_priority": "high",
        "common_faults": [
            "Telegraphing by dipping the shoulder too obviously",
            "Throwing the uppercut from too far away — it's a close-range punch",
            "Rising up on the toes — losing base and power",
            "Dropping the rear hand while throwing",
        ],
    },
    "rear_uppercut": {
        "name": "Rear Uppercut",
        "ideal_elbow_extension": (60, 100),
        "ideal_shoulder_angle": (40, 80),
        "hip_rotation_expected": "significant",
        "rear_hand_position": "n/a",
        "snap_back_priority": "high",
        "common_faults": [
            "No leg drive — power should come from the legs through the hips",
            "Leaning back while throwing — shifts weight off balance",
            "Dropping the lead hand during the punch",
            "Throwing from outside range — uppercuts are inside punches",
        ],
    },
}
