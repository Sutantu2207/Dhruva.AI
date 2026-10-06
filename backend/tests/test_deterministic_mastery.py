"""Test suite for deterministic concept mastery calculations."""

import pytest
from app.domains.mastery.engine import (
    calculate_mastery_tier,
    compute_updated_mastery,
    MasteryTier,
)


def test_mastery_tier_classification():
    """Validates deterministic tier boundaries."""
    assert calculate_mastery_tier(0.20) == MasteryTier.NOVICE
    assert calculate_mastery_tier(0.39) == MasteryTier.NOVICE
    assert calculate_mastery_tier(0.40) == MasteryTier.COMPETENT
    assert calculate_mastery_tier(0.69) == MasteryTier.COMPETENT
    assert calculate_mastery_tier(0.70) == MasteryTier.PROFICIENT
    assert calculate_mastery_tier(0.89) == MasteryTier.PROFICIENT
    assert calculate_mastery_tier(0.90) == MasteryTier.MASTER
    assert calculate_mastery_tier(1.00) == MasteryTier.MASTER


def test_compute_updated_mastery_progression():
    """Ensures deterministic updating follows mathematical bounds."""
    # Start at 0.50, score 1.0 on new assessment with weight 0.2
    # Expected: (0.50 * 0.8) + (1.0 * 0.2) = 0.40 + 0.20 = 0.60
    new_score = compute_updated_mastery(current_score=0.50, assessment_score=1.0, weight=0.20)
    assert new_score == 0.60


def test_mastery_clamped_between_zero_and_one():
    """Score cannot exceed 1.0 or drop below 0.0."""
    high = compute_updated_mastery(current_score=0.99, assessment_score=1.5, weight=0.5)
    assert high <= 1.0

    low = compute_updated_mastery(current_score=0.1, assessment_score=0.0, weight=0.5, decay_penalty=0.5)
    assert low >= 0.0
