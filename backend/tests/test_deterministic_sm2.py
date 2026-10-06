"""Test suite for deterministic SM-2 Spaced Repetition Engine."""

import pytest
from app.domains.mastery.sm2 import calculate_sm2


def test_sm2_first_successful_review():
    """First successful recall (grade 5) yields 1-day interval and 1 repetition."""
    result = calculate_sm2(grade=5, previous_repetitions=0, previous_interval=0, previous_easiness_factor=2.5)
    assert result.interval_days == 1
    assert result.repetitions == 1
    assert result.easiness_factor == 2.6


def test_sm2_second_successful_review():
    """Second successful recall yields 6-day interval and 2 repetitions."""
    result = calculate_sm2(grade=5, previous_repetitions=1, previous_interval=1, previous_easiness_factor=2.6)
    assert result.interval_days == 6
    assert result.repetitions == 2
    assert result.easiness_factor == 2.7


def test_sm2_third_review_progression():
    """Third review multiplies interval by the updated EF."""
    result = calculate_sm2(grade=4, previous_repetitions=2, previous_interval=6, previous_easiness_factor=2.7)
    # EF delta for grade 4 = 0.1 - (1)*(0.08 + 0.02) = 0.0 -> EF remains 2.7
    # Interval = round(6 * 2.7) = 16
    assert result.repetitions == 3
    assert result.easiness_factor == 2.7
    assert result.interval_days == 16


def test_sm2_failed_recall_resets_streak():
    """Failed recall (grade < 3) resets repetitions to 0 and interval to 1 day."""
    result = calculate_sm2(grade=1, previous_repetitions=5, previous_interval=45, previous_easiness_factor=2.5)
    assert result.repetitions == 0
    assert result.interval_days == 1
    # EF drops but remains >= 1.3
    assert result.easiness_factor < 2.5
    assert result.easiness_factor >= 1.3


def test_sm2_ef_floor_is_one_point_three():
    """Easiness factor is clamped to minimum 1.3 even with repeated zeroes."""
    ef = 1.4
    for _ in range(5):
        result = calculate_sm2(grade=0, previous_repetitions=0, previous_interval=1, previous_easiness_factor=ef)
        ef = result.easiness_factor
    assert ef == 1.3


def test_sm2_invalid_grade_raises_error():
    """Grades outside [0, 5] raise ValueError."""
    with pytest.raises(ValueError):
        calculate_sm2(grade=6)
    with pytest.raises(ValueError):
        calculate_sm2(grade=-1)
