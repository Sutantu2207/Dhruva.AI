"""Deterministic Assessment Evaluation & Scoring Engine (Domain 5).

Executes deterministic score calculations, rubric weighting, confidence metrics,
and exact decimal arithmetic without floating-point drift.
Zero reliance on LLMs for authoritative marks, grades, or completion status.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


# =========================================================================
# Legacy / Fast Evaluation Contracts (Preserved for backwards compatibility)
# =========================================================================

class QuestionEvaluation(BaseModel):
    question_id: str
    max_marks: float = Field(gt=0)
    awarded_marks: float = Field(ge=0)
    penalty_marks: float = Field(default=0.0, ge=0)
    weight: float = Field(default=1.0, gt=0)


class AssessmentScoreReport(BaseModel):
    total_max_marks: float
    total_raw_marks: float
    percentage: float = Field(ge=0.0, le=100.0)
    is_passing: bool
    confidence_score: float = Field(ge=0.0, le=1.0)
    section_breakdown: Dict[str, float]


def evaluate_submission(
    evaluations: List[QuestionEvaluation],
    passing_threshold_percentage: float = 50.0,
    confidence_factor: float = 1.0,
) -> AssessmentScoreReport:
    """Calculates deterministic score report based on strictly verified criteria."""
    if not evaluations:
        return AssessmentScoreReport(
            total_max_marks=0.0,
            total_raw_marks=0.0,
            percentage=0.0,
            is_passing=False,
            confidence_score=0.0,
            section_breakdown={},
        )

    total_max = sum(item.max_marks * item.weight for item in evaluations)
    total_raw = sum(
        max(0.0, (item.awarded_marks - item.penalty_marks)) * item.weight
        for item in evaluations
    )

    percentage = round((total_raw / total_max * 100.0), 2) if total_max > 0 else 0.0
    is_passing = percentage >= passing_threshold_percentage
    confidence = round(max(0.0, min(1.0, confidence_factor)), 4)

    return AssessmentScoreReport(
        total_max_marks=round(total_max, 2),
        total_raw_marks=round(total_raw, 2),
        percentage=min(100.0, max(0.0, percentage)),
        is_passing=is_passing,
        confidence_score=confidence,
        section_breakdown={"overall": percentage},
    )


# =========================================================================
# Domain 5 Production Deterministic Scoring Engine
# =========================================================================

class EvaluatedQuestionScore(BaseModel):
    question_version_id: str
    max_marks: Decimal
    awarded_marks: Decimal
    penalty_marks: Decimal = Decimal("0.00")
    is_correct: bool
    evaluation_type: str
    feedback: Optional[str] = None
    concepts: List[Dict[str, Any]] = []
    skills: List[Dict[str, Any]] = []


class DeterministicScoreSummary(BaseModel):
    maximum_marks: Decimal
    total_awarded_marks: Decimal
    total_penalties: Decimal
    net_marks: Decimal
    percentage: Decimal
    is_passed: bool
    grade: Optional[str] = None
    has_pending_manual_evaluation: bool = False


class AssessmentScoringEngine:
    """Pure deterministic scoring engine operating strictly with exact Decimal arithmetic."""

    @staticmethod
    def calculate_attempt_score(
        evaluated_questions: List[EvaluatedQuestionScore],
        passing_marks: Decimal = Decimal("0.00"),
        grade_rules: Optional[List[Dict[str, Any]]] = None,
        allow_net_negative: bool = False,
    ) -> DeterministicScoreSummary:
        """Aggregates question scores and applies deterministic grade rules."""
        if not evaluated_questions:
            return DeterministicScoreSummary(
                maximum_marks=Decimal("0.00"),
                total_awarded_marks=Decimal("0.00"),
                total_penalties=Decimal("0.00"),
                net_marks=Decimal("0.00"),
                percentage=Decimal("0.00"),
                is_passed=False,
                grade="F",
                has_pending_manual_evaluation=False,
            )

        total_max = sum((q.max_marks for q in evaluated_questions), Decimal("0.00"))
        total_awarded = sum((q.awarded_marks for q in evaluated_questions), Decimal("0.00"))
        total_penalties = sum((q.penalty_marks for q in evaluated_questions), Decimal("0.00"))

        raw_net = total_awarded - total_penalties
        if not allow_net_negative:
            net_marks = max(Decimal("0.00"), raw_net)
        else:
            net_marks = raw_net

        # Bound net marks to max marks
        net_marks = min(total_max, net_marks)

        if total_max > Decimal("0.00"):
            raw_pct = (net_marks / total_max) * Decimal("100.00")
            percentage = raw_pct.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            percentage = max(Decimal("0.00"), min(Decimal("100.00"), percentage))
        else:
            percentage = Decimal("0.00")

        is_passed = net_marks >= passing_marks
        has_manual = any(q.evaluation_type == "manual" for q in evaluated_questions)

        # Calculate Grade
        grade = AssessmentScoringEngine.resolve_grade(percentage, grade_rules)

        return DeterministicScoreSummary(
            maximum_marks=total_max.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            total_awarded_marks=total_awarded.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            total_penalties=total_penalties.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            net_marks=net_marks.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            percentage=percentage,
            is_passed=is_passed,
            grade=grade,
            has_pending_manual_evaluation=has_manual,
        )

    @staticmethod
    def resolve_grade(
        percentage: Decimal,
        grade_rules: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Determines grade string deterministically based on institutional rules."""
        if not grade_rules:
            # Standard institutional fallback scale
            if percentage >= Decimal("90.00"):
                return "A+"
            elif percentage >= Decimal("80.00"):
                return "A"
            elif percentage >= Decimal("70.00"):
                return "B"
            elif percentage >= Decimal("60.00"):
                return "C"
            elif percentage >= Decimal("50.00"):
                return "D"
            else:
                return "F"

        for rule in sorted(grade_rules, key=lambda r: float(r.get("min_percentage", 0)), reverse=True):
            min_p = Decimal(str(rule.get("min_percentage", 0)))
            max_p = Decimal(str(rule.get("max_percentage", 100)))
            if percentage >= min_p and percentage <= max_p:
                return str(rule.get("grade", "F"))

        return "F"
