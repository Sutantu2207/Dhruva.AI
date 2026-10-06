"""Deterministic Learning Priority Engine & Daily Mission Generator."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from app.domains.mastery.config import PriorityWeightConfig, DEFAULT_KNOWLEDGE_CONFIG


class ConceptStateContext(BaseModel):
    """Contextual metrics for an individual concept required to evaluate priority."""
    concept_id: str
    concept_name: str
    mastery: Optional[Decimal] = None
    retention_estimate: Decimal = Decimal("1.0000")
    review_status: str = "upcoming"  # overdue, due, upcoming, completed
    prerequisite_health: str = "healthy"  # healthy, partial, weak, unknown
    prerequisite_readiness: Optional[Decimal] = None
    trend: str = "stable"
    has_recent_failure: bool = False
    evidence_count: int = 0
    lesson_id: Optional[str] = None
    assessment_id: Optional[str] = None


class PriorityEvaluationResult(BaseModel):
    """Evaluated learning priority result for a single concept."""
    concept_id: str
    concept_name: str
    priority_score: Decimal  # [0.0000, 1.0000]
    reason_codes: List[str]
    mastery_gap: Decimal
    retention_risk: Decimal
    prerequisite_readiness: Decimal
    recommended_task_type: str  # review, practice, lesson, assessment
    reference_lesson_id: Optional[str] = None
    reference_assessment_id: Optional[str] = None


class DailyMissionTask(BaseModel):
    """Structured, reproducible learning task for student daily workflow."""
    task_id: str
    task_type: str  # review, practice, lesson, assessment
    title: str
    concept_id: str
    concept_name: str
    priority_score: float
    reason_codes: List[str]
    reference_id: Optional[str] = None
    estimated_minutes: int = 15


class LearningPriorityEngine:
    """Pure deterministic engine computing student learning priorities and daily missions."""

    @staticmethod
    def evaluate_concept_priority(
        ctx: ConceptStateContext,
        weights: PriorityWeightConfig = DEFAULT_KNOWLEDGE_CONFIG.priority_weights,
    ) -> PriorityEvaluationResult:
        """Evaluates deterministic priority score [0.0, 1.0] and assigns machine-readable reason codes."""
        reason_codes: List[str] = []

        # 1. Mastery Gap Component
        if ctx.mastery is None:
            mastery_val = 0.50  # Neutral prior for unobserved concepts
            reason_codes.append("INSUFFICIENT_EVIDENCE")
        else:
            mastery_val = float(ctx.mastery)
            if mastery_val < 0.60:
                reason_codes.append("MASTERY_LOW")

        mastery_gap_val = max(0.0, 1.0 - mastery_val)

        # 2. Retention Risk Component
        retention_val = float(ctx.retention_estimate)
        retention_risk_val = max(0.0, 1.0 - retention_val)
        if retention_val < 0.60:
            reason_codes.append("RETENTION_LOW")

        # 3. Review Urgency Component
        urgency_val = 0.0
        if ctx.review_status == "overdue":
            urgency_val = 1.00
            reason_codes.append("REVIEW_OVERDUE")
        elif ctx.review_status == "due":
            urgency_val = 0.70
            reason_codes.append("REVIEW_DUE")
        elif ctx.review_status == "upcoming":
            urgency_val = 0.20

        # 4. Prerequisite Weakness Component
        prereq_weakness_val = 0.0
        prereq_readiness_val = 1.0
        if ctx.prerequisite_health == "weak":
            prereq_weakness_val = 1.00
            prereq_readiness_val = 0.30
            reason_codes.append("PREREQUISITE_WEAK")
        elif ctx.prerequisite_health == "partial":
            prereq_weakness_val = 0.50
            prereq_readiness_val = 0.60
        elif ctx.prerequisite_readiness is not None:
            prereq_readiness_val = float(ctx.prerequisite_readiness)

        # 5. Recent Failure Component
        recent_failure_val = 0.0
        if ctx.has_recent_failure:
            recent_failure_val = 1.00
            reason_codes.append("RECENT_FAILURE")

        # 6. Trend Signal
        if ctx.trend in ("declining", "strongly_declining"):
            reason_codes.append("MASTERY_DECLINING")

        # Weighted Priority Formula
        raw_score = (
            float(weights.mastery_gap) * mastery_gap_val
            + float(weights.retention_risk) * retention_risk_val
            + float(weights.review_urgency) * urgency_val
            + float(weights.prerequisite_weakness) * prereq_weakness_val
            + float(weights.recent_failure) * recent_failure_val
        )
        clamped_score = max(0.0, min(1.0, raw_score))
        priority_decimal = Decimal(str(round(clamped_score, 4)))

        # Recommended Task Type selection
        if ctx.review_status in ("overdue", "due") or retention_val < 0.50:
            task_type = "review"
        elif ctx.prerequisite_health == "weak":
            task_type = "lesson"
        elif ctx.mastery is not None and float(ctx.mastery) >= 0.70:
            task_type = "practice"
        else:
            task_type = "lesson" if ctx.lesson_id else "practice"

        return PriorityEvaluationResult(
            concept_id=ctx.concept_id,
            concept_name=ctx.concept_name,
            priority_score=priority_decimal,
            reason_codes=reason_codes,
            mastery_gap=Decimal(str(round(mastery_gap_val, 4))),
            retention_risk=Decimal(str(round(retention_risk_val, 4))),
            prerequisite_readiness=Decimal(str(round(prereq_readiness_val, 4))),
            recommended_task_type=task_type,
            reference_lesson_id=ctx.lesson_id,
            reference_assessment_id=ctx.assessment_id,
        )

    @staticmethod
    def generate_daily_mission(
        evaluated_concepts: List[PriorityEvaluationResult],
        max_tasks: int = 5,
    ) -> List[DailyMissionTask]:
        """Generates a deterministic daily mission deduplicating concepts and prioritizing urgency."""
        # Sort by priority score descending
        sorted_evals = sorted(evaluated_concepts, key=lambda x: x.priority_score, reverse=True)

        mission_tasks: List[DailyMissionTask] = []
        seen_concepts = set()

        task_counter = 1
        for item in sorted_evals:
            if item.concept_id in seen_concepts:
                continue

            seen_concepts.add(item.concept_id)

            title = f"{item.recommended_task_type.capitalize()}: {item.concept_name}"
            ref_id = item.reference_lesson_id or item.reference_assessment_id

            mission_tasks.append(
                DailyMissionTask(
                    task_id=f"mission-task-{task_counter}",
                    task_type=item.recommended_task_type,
                    title=title,
                    concept_id=item.concept_id,
                    concept_name=item.concept_name,
                    priority_score=float(item.priority_score),
                    reason_codes=item.reason_codes,
                    reference_id=ref_id,
                    estimated_minutes=15,
                )
            )

            task_counter += 1
            if len(mission_tasks) >= max_tasks:
                break

        return mission_tasks
