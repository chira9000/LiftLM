from datetime import datetime, timedelta, timezone

from app.services.progression.engine import (
    _score_consistency,
    _score_progression,
    _score_recent_performance,
    _score_rpe,
    _score_volume_trend,
)


def _days_ago(n: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=n)


class TestConsistency:
    def test_no_sessions(self):
        assert _score_consistency([]) == 0.0

    def test_twice_a_week_for_eight_weeks_is_perfect(self):
        sessions = [_days_ago(d) for d in range(0, 56, 3)][:16]
        assert _score_consistency(sessions) == 100.0

    def test_sessions_outside_window_are_ignored(self):
        assert _score_consistency([_days_ago(100), _days_ago(120)]) == 0.0

    def test_naive_datetimes_are_treated_as_utc(self):
        naive = (datetime.now(timezone.utc) - timedelta(days=1)).replace(tzinfo=None)
        assert _score_consistency([naive]) > 0


class TestRpe:
    def test_sweet_spot(self):
        assert _score_rpe(7.0) == _score_rpe(8.5) == 100.0

    def test_unknown_rpe_is_neutral(self):
        assert _score_rpe(None) == 60.0

    def test_too_easy_scores_below_sweet_spot(self):
        assert _score_rpe(5.0) < 100.0

    def test_grinding_is_penalized_but_floored(self):
        assert _score_rpe(9.5) < 100.0
        assert _score_rpe(12.0) == 30.0


class TestVolumeTrend:
    def test_insufficient_data_is_neutral(self):
        assert _score_volume_trend([1000]) == 50.0

    def test_rising_volume_scores_above_neutral(self):
        assert _score_volume_trend([1000, 1000, 1000, 1200, 1200, 1200]) > 50

    def test_falling_volume_scores_below_neutral(self):
        assert _score_volume_trend([1200, 1200, 1200, 1000, 1000, 1000]) < 50

    def test_clamped_to_0_100(self):
        assert _score_volume_trend([100, 100, 100, 1000, 1000, 1000]) == 100
        assert _score_volume_trend([1000, 1000, 1000, 1, 1, 1]) == 0


class TestProgression:
    def test_flat(self):
        assert _score_progression([200, 200]) == 50

    def test_ten_percent_gain_maxes_out(self):
        assert _score_progression([200, 220]) == 70
        assert _score_progression([200, 300]) == 100


class TestRecentPerformance:
    def test_improved(self):
        assert _score_recent_performance([200, 205]) == 85

    def test_unchanged(self):
        assert _score_recent_performance([200, 200]) == 65

    def test_regressed_is_floored(self):
        assert _score_recent_performance([200, 100]) == 30
