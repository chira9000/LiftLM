import pytest

from app.services.llm.intent_classifier import classify_intent
from app.services.llm.muscle_groups import detect_muscle_groups, parent_muscle_group


class TestMuscleGroups:
    def test_detects_synonyms(self):
        assert detect_muscle_groups("my pecs and delts are sore") == ["chest", "shoulders"]

    def test_whole_word_matching(self):
        # "abs" must not match inside "absolutely", "back" not inside "backpack"
        assert detect_muscle_groups("absolutely, grab my backpack") == []

    def test_no_match(self):
        assert detect_muscle_groups("what time is it") == []

    @pytest.mark.parametrize("stored,expected", [
        ("Biceps", "arms"), ("quads", "legs"), ("lower back", "back"), ("chest", "chest"),
    ])
    def test_parent_rollup(self, stored, expected):
        assert parent_muscle_group(stored) == expected


class TestIntentClassifier:
    @pytest.mark.parametrize("message,intent", [
        ("My bench has been stuck for weeks", "PLATEAU"),
        ("How much protein should I eat?", "NUTRITION"),
        ("What's a good 4 day split?", "PROGRAMMING"),
        ("What's a substitute for barbell rows?", "EQUIPMENT"),
        ("hello", "GENERAL"),
        ("asdfgh", "UNKNOWN"),
    ])
    def test_category(self, message, intent):
        assert classify_intent(message)["intent"] == intent

    def test_plateau_beats_lower_priority_categories(self):
        # mentions a body part and a goal, but the plateau signal wins
        result = classify_intent("My arms stopped growing and I want more size")
        assert result == {"intent": "PLATEAU", "body_part": "arms", "goal": "hypertrophy"}
