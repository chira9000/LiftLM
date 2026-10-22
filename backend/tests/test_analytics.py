import pytest

from app.services.analytics.engine import estimate_1rm


def test_single_rep_is_the_lift_itself():
    assert estimate_1rm(225, 1) == 225


def test_epley_formula():
    # 200 x 5 -> 200 * (1 + 5/30)
    assert estimate_1rm(200, 5) == pytest.approx(233.33, abs=0.01)


@pytest.mark.parametrize("weight,reps", [(0, 5), (-10, 5), (135, 0), (135, -1)])
def test_invalid_input_returns_zero(weight, reps):
    assert estimate_1rm(weight, reps) == 0.0


def test_more_reps_at_same_weight_means_higher_estimate():
    assert estimate_1rm(185, 8) > estimate_1rm(185, 5)
