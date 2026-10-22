"""Keyword-based muscle group detection.

No training data yet, so this is a deterministic fallback: map common gym
terminology to the canonical `muscle_group` values used on `Exercise` rows
(see app.seed.EXERCISES), so a message like "what should I do for chest"
can be matched against exercises without an LLM having to infer it.
"""

import re

MUSCLE_GROUP_KEYWORDS: dict[str, list[str]] = {
    "chest": ["chest", "chests", "pec", "pecs", "pectoral", "pectorals"],
    "back": ["back", "lat", "lats", "latissimus", "trap", "traps", "trapezius"],
    "legs": [
        "leg", "legs", "quad", "quads", "quadriceps",
        "hamstring", "hamstrings", "glute", "glutes", "calf", "calves",
    ],
    "shoulders": ["shoulder", "shoulders", "delt", "delts", "deltoid", "deltoids"],
    "arms": ["arm", "arms", "bicep", "biceps", "tricep", "triceps", "forearm", "forearms"],
    "core": ["core", "ab", "abs", "abdominal", "abdominals", "oblique", "obliques"],
}


# Finer-grained `Exercise.muscle_group` values (see app.exercise_catalog) -> canonical group.
MUSCLE_GROUP_PARENTS: dict[str, str] = {
    "biceps": "arms", "triceps": "arms", "forearms": "arms",
    "quads": "legs", "hamstrings": "legs", "glutes": "legs", "calves": "legs", "adductors": "legs",
    "traps": "back", "lower back": "back",
}


def parent_muscle_group(muscle_group: str) -> str:
    """Roll a stored `Exercise.muscle_group` up to its canonical group (identity if already canonical)."""
    muscle_group = muscle_group.lower()
    return MUSCLE_GROUP_PARENTS.get(muscle_group, muscle_group)


def detect_muscle_groups(text: str) -> list[str]:
    """Return canonical muscle groups mentioned in `text`, in order of first mention."""
    text_lower = text.lower()
    found: list[str] = []
    for canonical, keywords in MUSCLE_GROUP_KEYWORDS.items():
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                found.append(canonical)
                break
    return found
