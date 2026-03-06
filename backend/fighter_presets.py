"""
Fighter style presets based on known boxing legends.
Each preset defines characteristic traits that the analysis engine
compares against to determine style similarity.
"""

FIGHTER_PRESETS = {
    "mike_tyson": {
        "name": "Mike Tyson",
        "nickname": "Iron Mike",
        "era": "1985-2005",
        "stance": "orthodox",
        "style": "Peek-a-Boo / Pressure Fighter",
        "traits": {
            "head_movement": 0.95,      # Exceptional head movement, bobbing and weaving
            "guard_tightness": 0.95,     # Peek-a-boo: very tight, high guard
            "aggression": 0.95,          # Extreme forward pressure
            "punch_power": 0.98,         # One of the hardest hitters ever
            "punch_speed": 0.90,         # Very fast combinations
            "combination_frequency": 0.90,# Rapid multi-punch combos
            "body_work": 0.85,           # Devastating body shots
            "footwork_lateral": 0.60,    # Less lateral, more forward
            "footwork_forward": 0.95,    # Constant forward pressure
            "crouch_level": 0.90,        # Very low crouch
            "counter_punching": 0.70,    # Primarily offensive
            "jab_usage": 0.50,           # Less jab-reliant
            "ring_cutting": 0.90,        # Expert at cutting off the ring
            "distance_control": 0.60,    # Prefers inside fighting
        },
        "signature_moves": ["peek-a-boo guard", "bobbing", "weaving", "lead hook", "uppercut"],
        "description": "Explosive inside fighter with devastating power. Uses the peek-a-boo "
                       "style with tight guard, constant head movement, and explosive combinations. "
                       "Known for closing distance rapidly and finishing fights with hooks and uppercuts."
    },

    "muhammad_ali": {
        "name": "Muhammad Ali",
        "nickname": "The Greatest",
        "era": "1960-1981",
        "stance": "orthodox",
        "style": "Out-Fighter / Counter Puncher",
        "traits": {
            "head_movement": 0.80,
            "guard_tightness": 0.40,     # Hands often low, relied on reflexes
            "aggression": 0.55,
            "punch_power": 0.70,
            "punch_speed": 0.95,         # Lightning fast hands
            "combination_frequency": 0.80,
            "body_work": 0.40,
            "footwork_lateral": 0.98,    # "Float like a butterfly"
            "footwork_forward": 0.60,
            "crouch_level": 0.20,        # Stood very tall
            "counter_punching": 0.90,    # Elite counter puncher
            "jab_usage": 0.95,           # One of the best jabs in history
            "ring_cutting": 0.50,
            "distance_control": 0.95,    # Masterful range management
        },
        "signature_moves": ["jab", "straight right", "pull counter", "lateral movement"],
        "description": "Graceful out-fighter who relied on speed, footwork, and reflexes rather "
                       "than a tight guard. Masterful jab, exceptional lateral movement, and the "
                       "ability to make opponents miss while countering with precision."
    },

    "floyd_mayweather": {
        "name": "Floyd Mayweather Jr.",
        "nickname": "Money / Pretty Boy",
        "era": "1996-2017",
        "stance": "orthodox",
        "style": "Defensive Counter Puncher",
        "traits": {
            "head_movement": 0.85,
            "guard_tightness": 0.90,     # Shoulder roll / Philly shell
            "aggression": 0.35,
            "punch_power": 0.55,
            "punch_speed": 0.90,
            "combination_frequency": 0.65,
            "body_work": 0.50,
            "footwork_lateral": 0.85,
            "footwork_forward": 0.40,
            "crouch_level": 0.50,
            "counter_punching": 0.98,    # Greatest counter puncher
            "jab_usage": 0.80,
            "ring_cutting": 0.70,
            "distance_control": 0.95,
        },
        "signature_moves": ["shoulder roll", "pull counter", "check hook", "lead right"],
        "description": "Defensive genius using the shoulder roll / Philly shell guard. "
                       "Exceptional at making opponents miss and making them pay with sharp counters. "
                       "Outstanding ring IQ, timing, and distance management."
    },

    "manny_pacquiao": {
        "name": "Manny Pacquiao",
        "nickname": "Pac-Man",
        "era": "1995-2021",
        "stance": "southpaw",
        "style": "Aggressive Swarmer",
        "traits": {
            "head_movement": 0.70,
            "guard_tightness": 0.55,
            "aggression": 0.95,
            "punch_power": 0.85,
            "punch_speed": 0.95,
            "combination_frequency": 0.95,  # Blinding combinations
            "body_work": 0.75,
            "footwork_lateral": 0.80,
            "footwork_forward": 0.90,
            "crouch_level": 0.60,
            "counter_punching": 0.60,
            "jab_usage": 0.65,
            "ring_cutting": 0.80,
            "distance_control": 0.65,
        },
        "signature_moves": ["straight left", "lead right hook", "rapid combinations", "angle changes"],
        "description": "Explosive southpaw swarmer with blinding hand speed and power in both hands. "
                       "Uses angles and footwork to create openings, then overwhelms opponents with "
                       "rapid-fire combinations from unusual angles."
    },

    "canelo_alvarez": {
        "name": "Canelo Alvarez",
        "nickname": "Canelo",
        "era": "2005-present",
        "stance": "orthodox",
        "style": "Counter Puncher / Pressure Fighter",
        "traits": {
            "head_movement": 0.90,
            "guard_tightness": 0.85,
            "aggression": 0.70,
            "punch_power": 0.90,
            "punch_speed": 0.80,
            "combination_frequency": 0.75,
            "body_work": 0.90,           # Elite body puncher
            "footwork_lateral": 0.70,
            "footwork_forward": 0.75,
            "crouch_level": 0.65,
            "counter_punching": 0.90,
            "jab_usage": 0.60,
            "ring_cutting": 0.85,
            "distance_control": 0.80,
        },
        "signature_moves": ["counter right hand", "body shots", "uppercut", "head movement"],
        "description": "Technically elite counter puncher with devastating body work. "
                       "Uses excellent head movement to slip shots and counters with precision. "
                       "Combines patience with explosive power, especially to the body."
    },

    "sugar_ray_leonard": {
        "name": "Sugar Ray Leonard",
        "nickname": "Sugar Ray",
        "era": "1977-1997",
        "stance": "orthodox",
        "style": "Boxer-Puncher",
        "traits": {
            "head_movement": 0.80,
            "guard_tightness": 0.70,
            "aggression": 0.75,
            "punch_power": 0.80,
            "punch_speed": 0.95,
            "combination_frequency": 0.85,
            "body_work": 0.70,
            "footwork_lateral": 0.90,
            "footwork_forward": 0.80,
            "crouch_level": 0.45,
            "counter_punching": 0.80,
            "jab_usage": 0.85,
            "ring_cutting": 0.75,
            "distance_control": 0.85,
        },
        "signature_moves": ["jab", "combinations", "lateral movement", "flurries"],
        "description": "Complete boxer-puncher with dazzling hand speed and ring IQ. "
                       "Could fight on the inside or outside, adapting his style to any opponent. "
                       "Known for his flashy combinations and ability to turn fights around."
    },

    "joe_frazier": {
        "name": "Joe Frazier",
        "nickname": "Smokin' Joe",
        "era": "1965-1981",
        "stance": "orthodox",
        "style": "Swarmer / Pressure Fighter",
        "traits": {
            "head_movement": 0.85,
            "guard_tightness": 0.80,
            "aggression": 0.98,
            "punch_power": 0.90,
            "punch_speed": 0.75,
            "combination_frequency": 0.80,
            "body_work": 0.90,
            "footwork_lateral": 0.40,
            "footwork_forward": 0.95,
            "crouch_level": 0.90,         # Very low crouch
            "counter_punching": 0.30,
            "jab_usage": 0.40,
            "ring_cutting": 0.85,
            "distance_control": 0.40,
        },
        "signature_moves": ["left hook", "body attack", "bobbing", "forward pressure"],
        "description": "Relentless pressure fighter with a devastating left hook. Fought from a deep "
                       "crouch, constantly bobbing and weaving forward. Would wear opponents down with "
                       "non-stop body work and overwhelm them with aggression."
    },

    "lennox_lewis": {
        "name": "Lennox Lewis",
        "nickname": "The Lion",
        "era": "1989-2003",
        "stance": "orthodox",
        "style": "Technical Boxer / Out-Fighter",
        "traits": {
            "head_movement": 0.60,
            "guard_tightness": 0.75,
            "aggression": 0.55,
            "punch_power": 0.90,
            "punch_speed": 0.70,
            "combination_frequency": 0.55,
            "body_work": 0.50,
            "footwork_lateral": 0.65,
            "footwork_forward": 0.60,
            "crouch_level": 0.30,
            "counter_punching": 0.75,
            "jab_usage": 0.95,           # Elite jab
            "ring_cutting": 0.65,
            "distance_control": 0.90,
        },
        "signature_moves": ["jab", "straight right", "uppercut", "distance control"],
        "description": "Tall, rangy boxer who controlled fights with one of the best jabs in "
                       "heavyweight history. Used his reach and technical skill to keep opponents "
                       "at distance, then punished them with power shots when they came in."
    },
}


def get_all_presets():
    """Return all fighter presets."""
    return FIGHTER_PRESETS


def get_preset(fighter_key):
    """Return a specific fighter preset."""
    return FIGHTER_PRESETS.get(fighter_key)


def get_preset_summary_list():
    """Return a list of fighter summaries for the frontend."""
    summaries = []
    for key, preset in FIGHTER_PRESETS.items():
        summaries.append({
            "key": key,
            "name": preset["name"],
            "nickname": preset["nickname"],
            "style": preset["style"],
            "stance": preset["stance"],
            "era": preset["era"],
            "signature_moves": preset["signature_moves"],
            "description": preset["description"],
        })
    return summaries


def match_style_to_presets(analysis_traits):
    """Compare analyzed traits against all presets and return similarity scores.

    Args:
        analysis_traits: dict with same keys as preset traits, values 0-1

    Returns:
        List of (fighter_key, similarity_score, preset) sorted by similarity descending.
    """
    results = []
    for key, preset in FIGHTER_PRESETS.items():
        preset_traits = preset["traits"]
        total_diff = 0
        count = 0
        for trait_key, preset_val in preset_traits.items():
            if trait_key in analysis_traits:
                diff = abs(preset_val - analysis_traits[trait_key])
                total_diff += diff
                count += 1
        if count > 0:
            avg_diff = total_diff / count
            similarity = max(0, 1.0 - avg_diff)
            results.append((key, round(similarity * 100, 1), preset))

    results.sort(key=lambda x: x[1], reverse=True)
    return results
