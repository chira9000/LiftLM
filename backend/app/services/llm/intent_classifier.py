"""Keyword-based coaching-intent classifier.

Same deterministic approach as intent.py / muscle_groups.py: no training
data yet, so classify the user's message into one of a fixed set of
coaching-intent categories via priority-ordered keyword matching, plus
lightweight body_part / goal extraction, so the LLM gets an unambiguous
"what kind of question is this" signal instead of having to infer it.
"""

import re

from app.services.llm.muscle_groups import detect_muscle_groups

INTENT_PROGRAMMING = "PROGRAMMING"
INTENT_EXERCISE_SELECTION = "EXERCISE_SELECTION"
INTENT_TECHNIQUE = "TECHNIQUE"
INTENT_PROGRESSION = "PROGRESSION"
INTENT_PLATEAU = "PLATEAU"
INTENT_RECOVERY = "RECOVERY"
INTENT_NUTRITION = "NUTRITION"
INTENT_EQUIPMENT = "EQUIPMENT"
INTENT_WORKOUT_ANALYSIS = "WORKOUT_ANALYSIS"
INTENT_GENERAL = "GENERAL"
INTENT_UNKNOWN = "UNKNOWN"

# Checked in order — the first category whose keywords hit wins, since a
# message can trip more than one bucket (e.g. "my arms are stuck" is both
# plateau-shaped and mentions a body part). Put the most specific / highest
# -signal categories first.
INTENT_KEYWORDS: list[tuple[str, list[str]]] = [
    (INTENT_PLATEAU, [
        "plateau", "plateaued", "plateauing", "stuck", "stalled", "stall",
        "stalling", "not progressing", "no progress", "flatlined", "flatline",
        "stopped growing", "stopped gaining", "hit a wall", "hit a plateau",
    ]),
    (INTENT_RECOVERY, [
        "recovery", "recover", "recovering", "rest day", "rest days",
        "sleep", "sore", "soreness", "deload", "deloading", "overtrained",
        "overtraining", "burnt out", "burnout", "fatigued", "fatigue",
        "injury", "injured", "pain", "hurts", "hurt", "hurting",
    ]),
    (INTENT_NUTRITION, [
        "nutrition", "diet", "protein", "calories", "calorie", "macros",
        "carbs", "carbohydrate", "carbohydrates", "bulking", "bulk",
        "cutting", "cut weight", "meal", "meals", "eating", "eat before",
        "eat after", "supplement", "supplements", "creatine",
    ]),
    (INTENT_EQUIPMENT, [
        "equipment", "barbell", "dumbbell", "dumbbells", "kettlebell",
        "kettlebells", "resistance band", "bands", "machine", "machines",
        "home gym", "no gym", "don't have access", "gym doesn't have",
        "smith machine",
    ]),
    (INTENT_TECHNIQUE, [
        "form", "technique", "cue", "cues", "proper way", "how do i do",
        "am i doing", "doing it right", "bar path", "depth", "setup for",
    ]),
    (INTENT_PROGRESSION, [
        "progress", "progression", "increase weight", "add weight",
        "next weight", "how much weight", "add reps", "progressive overload",
        "1rm", "one rep max", "max out", "get stronger", "increase my",
    ]),
    (INTENT_WORKOUT_ANALYSIS, [
        "how did i do", "analyze my", "analyse my", "review my workout",
        "last workout", "this week", "my volume", "my trend", "my trends",
        "how am i doing", "summary of my", "look at my",
    ]),
    (INTENT_PROGRAMMING, [
        "program", "programming", "routine", "split", "periodization",
        "training plan", "workout plan", "how many days", "how often should i",
        "schedule", "mesocycle", "microcycle",
    ]),
    (INTENT_EXERCISE_SELECTION, [
        "what exercise", "which exercise", "alternative", "substitute",
        "swap", "best exercise", "what should i do for", "replace",
    ]),
    (INTENT_GENERAL, [
        "hi", "hello", "hey", "thanks", "thank you", "what can you do",
        "who are you", "help me",
    ]),
]

GOAL_KEYWORDS: dict[str, list[str]] = {
    "hypertrophy": [
        "hypertrophy", "muscle", "bulk", "bulking", "size", "mass",
        "grow", "growing", "growth",
    ],
    "strength": [
        "strength", "stronger", "get stronger", "1rm", "one rep max",
        "max out", "powerlifting",
    ],
    "fat_loss": ["lose fat", "cut", "cutting", "lean out", "fat loss", "weight loss"],
    "endurance": ["endurance", "stamina", "conditioning"],
    "technique": ["technique", "form"],
}


def _match_any(text: str, keywords: list[str]) -> bool:
    return any(re.search(rf"\b{re.escape(kw)}\b", text) for kw in keywords)


def _classify_category(text: str) -> str:
    for category, keywords in INTENT_KEYWORDS:
        if _match_any(text, keywords):
            return category
    return INTENT_UNKNOWN


def _extract_goal(text: str) -> str | None:
    for canonical, keywords in GOAL_KEYWORDS.items():
        if _match_any(text, keywords):
            return canonical
    return None


def classify_intent(message: str) -> dict:
    """Classify `message` into a coaching-intent category with body_part / goal.

    Always returns a dict shaped like:
        {"intent": "PLATEAU", "body_part": "arms", "goal": "hypertrophy"}
    `intent` falls back to "UNKNOWN"; `body_part` / `goal` are None when
    nothing in the message matches.
    """
    text = message.lower()
    body_parts = detect_muscle_groups(message)

    return {
        "intent": _classify_category(text),
        "body_part": body_parts[0] if body_parts else None,
        "goal": _extract_goal(text),
    }
