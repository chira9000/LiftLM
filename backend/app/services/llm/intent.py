"""Keyword-based structured intent extraction.

No training data yet, so — same approach as muscle_groups.py — this is a
deterministic fallback: pull an { exercise, problem, weight, reps, goal,
timeframe, experience_level } shape out of the raw message with regex/keyword
matching, so the LLM gets an unambiguous structured signal instead of having
to infer it from free text itself.
"""

import re

PROBLEM_KEYWORDS: dict[str, list[str]] = {
    "plateau": [
        "plateau", "plateaued", "plateauing", "stuck", "stalled", "stall",
        "stalling", "not progressing", "no progress", "flatlined", "flatline",
    ],
    "pain": ["pain", "hurts", "hurt", "hurting", "sore", "soreness", "injury", "injured", "ache", "aching"],
    "form": ["form", "technique", "technic"],
    "regression": ["weaker", "regressed", "regression", "losing strength", "lost strength"],
    "fatigue": ["tired", "fatigued", "fatigue", "burnt out", "burnout", "overtrained", "overtraining"],
}

GOAL_KEYWORDS: dict[str, list[str]] = {
    "increase strength": ["strength", "stronger", "get stronger", "1rm", "one rep max", "max out"],
    "build muscle": ["muscle", "hypertrophy", "bulk", "bulking", "size", "mass"],
    "lose fat": ["lose fat", "cut", "cutting", "lean out", "fat loss", "weight loss"],
    "improve endurance": ["endurance", "stamina", "conditioning"],
    "improve technique": ["technique", "form"],
}

EXPERIENCE_KEYWORDS: dict[str, list[str]] = {
    "beginner": ["beginner", "new to lifting", "just started", "novice"],
    "intermediate": ["intermediate"],
    "advanced": ["advanced", "experienced"],
}

_COMBO_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:lbs?|kgs?)?\s*[x×]\s*(\d+)\b", re.IGNORECASE)
_WEIGHT_FOR_REPS_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:lbs?|kgs?)?\s+for\s+(\d+)\s*reps?\b", re.IGNORECASE)
_WEIGHT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:lbs?|pounds?|kgs?|kilograms?)\b", re.IGNORECASE)
_AT_WEIGHT_RE = re.compile(r"\bat\s+(\d+(?:\.\d+)?)\b", re.IGNORECASE)
_REPS_RE = re.compile(r"(\d+)\s*reps?\b", re.IGNORECASE)
_TIMEFRAME_RE = re.compile(r"(\d+)\s*(days?|weeks?|months?|years?)\b", re.IGNORECASE)

_EXERCISE_STOPWORDS = {"barbell", "dumbbell", "cable", "machine", "conventional", "smith"}
_WORD_RE = re.compile(r"[a-z0-9]+")


def _match_keyword_dict(text: str, mapping: dict[str, list[str]]) -> str | None:
    for canonical, keywords in mapping.items():
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text):
                return canonical
    return None


def _match_exercise(text: str, exercises: list[dict]) -> str | None:
    """Best-overlap match between message words and exercise-name words.

    Handles partial mentions ("squat" for "Barbell Back Squat") without a
    training set — just token overlap, ignoring generic equipment words.
    """
    text_words = set(_WORD_RE.findall(text))
    best_name: str | None = None
    best_score = 0
    for e in exercises:
        name_words = set(_WORD_RE.findall(e["name"].lower())) - _EXERCISE_STOPWORDS
        if not name_words:
            continue
        score = len(name_words & text_words)
        if score > best_score:
            best_score = score
            best_name = e["name"]
    return best_name


def extract_query_intent(message: str, exercises: list[dict]) -> dict | None:
    """Extract a structured intent dict from `message`, or None if nothing matched."""
    text = message.lower()

    exercise = _match_exercise(text, exercises)
    problem = _match_keyword_dict(text, PROBLEM_KEYWORDS)
    goal = _match_keyword_dict(text, GOAL_KEYWORDS)
    experience_level = _match_keyword_dict(text, EXPERIENCE_KEYWORDS)

    weight: float | None = None
    reps: int | None = None
    combo = _COMBO_RE.search(text)
    weight_for_reps = _WEIGHT_FOR_REPS_RE.search(text)
    if combo:
        weight = float(combo.group(1))
        reps = int(combo.group(2))
    elif weight_for_reps:
        weight = float(weight_for_reps.group(1))
        reps = int(weight_for_reps.group(2))
    else:
        w = _WEIGHT_RE.search(text) or _AT_WEIGHT_RE.search(text)
        if w:
            weight = float(w.group(1))
        r = _REPS_RE.search(text)
        if r:
            reps = int(r.group(1))

    timeframe: str | None = None
    tf = _TIMEFRAME_RE.search(text)
    if tf:
        timeframe = f"{tf.group(1)} {tf.group(2)}"

    if not any([exercise, problem, weight, reps, goal, timeframe, experience_level]):
        return None

    return {
        "exercise": exercise,
        "problem": problem,
        "weight": weight,
        "reps": reps,
        "goal": goal,
        "timeframe": timeframe,
        "experience_level": experience_level,
    }
