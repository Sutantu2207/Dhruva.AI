"""Test suite for deterministic assessment scoring."""

from app.domains.assessment.engine import (
    QuestionEvaluation,
    evaluate_submission,
)


def test_assessment_scoring_exactness():
    """Verifies that score calculation strictly aggregates weighted marks without hallucination."""
    evaluations = [
        QuestionEvaluation(question_id="q1", max_marks=10.0, awarded_marks=8.0, penalty_marks=0.0, weight=1.0),
        QuestionEvaluation(question_id="q2", max_marks=20.0, awarded_marks=15.0, penalty_marks=2.0, weight=1.0),
        QuestionEvaluation(question_id="q3", max_marks=10.0, awarded_marks=10.0, penalty_marks=0.0, weight=2.0),
    ]
    # Total max = (10*1) + (20*1) + (10*2) = 10 + 20 + 20 = 50.0
    # Raw marks:
    # q1: 8.0 * 1 = 8.0
    # q2: (15 - 2) * 1 = 13.0
    # q3: 10.0 * 2 = 20.0
    # Total raw = 8 + 13 + 20 = 41.0
    # Percentage = (41.0 / 50.0) * 100 = 82.0%
    report = evaluate_submission(evaluations, passing_threshold_percentage=60.0)
    assert report.total_max_marks == 50.0
    assert report.total_raw_marks == 41.0
    assert report.percentage == 82.0
    assert report.is_passing is True


def test_assessment_empty_submission():
    """Empty submission cleanly defaults to 0% and failing."""
    report = evaluate_submission([])
    assert report.total_max_marks == 0.0
    assert report.percentage == 0.0
    assert report.is_passing is False
