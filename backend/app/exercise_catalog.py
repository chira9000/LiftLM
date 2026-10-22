"""Exercise library, seeded into the `exercises` table on startup.

Each entry is (muscle_group, equipment, [exercise names]). Names are unique in
the DB, so an exercise listed under several muscle groups appears only under
the first one (e.g. Bulgarian Split Squat -> quads, not glutes).

`muscle_group` values here are finer-grained than the six canonical groups in
app.services.llm.muscle_groups; use `parent_muscle_group` to roll them up.
"""

CATALOG: list[tuple[str, str, list[str]]] = [
    # Chest
    ("chest", "barbell", ["Barbell Bench Press", "Incline Barbell Bench Press", "Decline Bench Press"]),
    ("chest", "dumbbell", [
        "Dumbbell Bench Press", "Incline Dumbbell Press", "Decline Dumbbell Press",
        "Dumbbell Fly", "Incline Dumbbell Fly",
    ]),
    ("chest", "machine", ["Machine Chest Press", "Incline Machine Press", "Pec Deck"]),
    ("chest", "smith machine", ["Smith Machine Bench Press", "Smith Machine Incline Press"]),
    ("chest", "cable", ["Cable Fly", "Low-to-High Cable Fly", "High-to-Low Cable Fly"]),
    ("chest", "bodyweight", ["Push-Up", "Weighted Push-Up", "Dip", "Chest Dip"]),

    # Back / lats
    ("back", "bodyweight", ["Pull-Up", "Chin-Up", "Neutral-Grip Pull-Up", "Inverted Row"]),
    ("back", "cable", [
        "Lat Pulldown", "Wide-Grip Lat Pulldown", "Close-Grip Lat Pulldown",
        "Neutral-Grip Lat Pulldown", "Single-Arm Lat Pulldown", "Straight-Arm Pulldown",
        "Seated Cable Row", "Wide-Grip Cable Row", "Single-Arm Cable Row",
    ]),
    ("back", "barbell", ["Barbell Row", "Pendlay Row", "T-Bar Row", "Meadows Row"]),
    ("back", "dumbbell", ["Dumbbell Row", "Chest-Supported Dumbbell Row", "Dumbbell Pullover"]),
    ("back", "machine", [
        "Chest-Supported T-Bar Row", "Machine Row", "High Row Machine", "Low Row Machine",
        "Machine Pullover",
    ]),

    # Shoulders
    ("shoulders", "barbell", ["Overhead Press", "Seated Barbell Shoulder Press", "Upright Row"]),
    ("shoulders", "dumbbell", [
        "Dumbbell Shoulder Press", "Arnold Press", "Dumbbell Lateral Raise", "Front Raise",
        "Rear-Delt Dumbbell Fly",
    ]),
    ("shoulders", "machine", ["Machine Shoulder Press", "Machine Lateral Raise", "Reverse Pec Deck"]),
    ("shoulders", "smith machine", ["Smith Machine Shoulder Press"]),
    ("shoulders", "cable", [
        "Cable Lateral Raise", "Leaning Cable Lateral Raise", "Cable Front Raise",
        "Cable Rear-Delt Fly", "Face Pull",
    ]),

    # Biceps
    ("biceps", "barbell", ["Barbell Curl", "Preacher Curl", "Reverse Curl"]),
    ("biceps", "ez bar", ["EZ-Bar Curl", "EZ-Bar Preacher Curl"]),
    ("biceps", "dumbbell", [
        "Dumbbell Curl", "Alternating Dumbbell Curl", "Hammer Curl", "Cross-Body Hammer Curl",
        "Incline Dumbbell Curl", "Dumbbell Preacher Curl", "Spider Curl", "Concentration Curl",
    ]),
    ("biceps", "machine", ["Machine Preacher Curl"]),
    ("biceps", "cable", ["Cable Curl", "Bayesian Cable Curl", "Single-Arm Cable Curl", "High Cable Curl"]),

    # Triceps
    ("triceps", "cable", [
        "Cable Triceps Pushdown", "Rope Pushdown", "Straight-Bar Pushdown", "Single-Arm Pushdown",
        "Reverse-Grip Pushdown", "Overhead Cable Triceps Extension", "Rope Overhead Extension",
        "Cable Triceps Kickback",
    ]),
    ("triceps", "dumbbell", ["Dumbbell Overhead Triceps Extension", "Dumbbell Skull Crusher", "Dumbbell Kickback"]),
    ("triceps", "barbell", ["Skull Crusher", "JM Press", "Close-Grip Bench Press"]),
    ("triceps", "ez bar", ["EZ-Bar Skull Crusher"]),
    ("triceps", "bodyweight", ["Triceps Dip"]),
    ("triceps", "machine", ["Assisted Dip", "Machine Dip"]),

    # Quads
    ("quads", "barbell", ["Back Squat", "Front Squat", "High-Bar Squat"]),
    ("quads", "machine", [
        "Hack Squat", "Pendulum Squat", "Leg Press", "Horizontal Leg Press",
        "Leg Extension", "Single-Leg Extension",
    ]),
    ("quads", "smith machine", ["Smith Machine Squat"]),
    ("quads", "dumbbell", [
        "Bulgarian Split Squat", "Front-Foot-Elevated Split Squat", "Walking Lunge", "Reverse Lunge",
        "Forward Lunge", "Step-Up", "Goblet Squat", "Heel-Elevated Goblet Squat",
    ]),
    ("quads", "bodyweight", ["Sissy Squat"]),

    # Hamstrings
    ("hamstrings", "barbell", ["Romanian Deadlift", "Stiff-Leg Deadlift", "Good Morning"]),
    ("hamstrings", "dumbbell", ["Dumbbell Romanian Deadlift"]),
    ("hamstrings", "machine", ["Seated Leg Curl", "Lying Leg Curl", "Standing Single-Leg Curl", "Glute-Ham Raise"]),
    ("hamstrings", "bodyweight", ["Nordic Hamstring Curl", "Stability-Ball Leg Curl"]),
    ("hamstrings", "cable", ["Cable Leg Curl"]),

    # Glutes
    ("glutes", "barbell", ["Barbell Hip Thrust"]),
    ("glutes", "smith machine", ["Smith Machine Hip Thrust"]),
    ("glutes", "machine", ["Machine Hip Thrust", "Machine Glute Kickback", "Hip Abduction Machine"]),
    ("glutes", "dumbbell", ["Dumbbell Hip Thrust"]),
    ("glutes", "bodyweight", ["Glute Bridge"]),
    ("glutes", "cable", ["Cable Pull-Through", "Cable Glute Kickback", "Cable Hip Abduction"]),

    # Calves
    ("calves", "machine", [
        "Standing Calf Raise", "Seated Calf Raise", "Leg Press Calf Raise", "Donkey Calf Raise",
        "Machine Calf Raise",
    ]),
    ("calves", "smith machine", ["Smith Machine Calf Raise"]),
    ("calves", "bodyweight", ["Single-Leg Calf Raise", "Tibialis Raise"]),

    # Abs / core
    ("core", "cable", ["Cable Crunch", "Pallof Press", "Cable Wood Chop"]),
    ("core", "machine", ["Machine Crunch"]),
    ("core", "bodyweight", [
        "Decline Sit-Up", "Hanging Leg Raise", "Hanging Knee Raise", "Captain's Chair Leg Raise",
        "Reverse Crunch", "Ab Wheel Rollout", "Plank", "Side Plank", "Weighted Plank",
        "Russian Twist", "Dead Bug", "Bird Dog",
    ]),

    # Traps / forearms / other
    ("traps", "dumbbell", ["Dumbbell Shrug"]),
    ("traps", "barbell", ["Barbell Shrug"]),
    ("traps", "machine", ["Machine Shrug"]),
    ("traps", "cable", ["Cable Shrug"]),
    ("forearms", "dumbbell", ["Farmer's Carry", "Wrist Curl", "Reverse Wrist Curl"]),
    ("forearms", "cable", ["Cable Wrist Curl"]),
    ("forearms", "wrist roller", ["Wrist Roller"]),
    ("forearms", "plate", ["Plate Pinch"]),
    ("forearms", "bodyweight", ["Dead Hang"]),
    ("adductors", "machine", ["Hip Adduction Machine"]),
    ("adductors", "cable", ["Cable Hip Adduction"]),
    ("lower back", "bodyweight", ["Back Extension"]),
    ("lower back", "machine", ["Reverse Hyperextension"]),
]


def catalog_exercises() -> list[tuple[str, str, str]]:
    """Flatten CATALOG into unique (name, muscle_group, equipment) rows, first listing wins."""
    seen: set[str] = set()
    rows: list[tuple[str, str, str]] = []
    for muscle_group, equipment, names in CATALOG:
        for name in names:
            if name in seen:
                continue
            seen.add(name)
            rows.append((name, muscle_group, equipment))
    return rows
