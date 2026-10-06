"""Deterministic Diagnostic Engine (Domain 10).

Determines WHY a remediation signal exists without psychologizing or speculation.
Strictly relies on observable academic distress:
- LOW_MASTERY
- LOW_RETENTION
- PREREQUISITE_GAP
- REPEATED_ASSESSMENT_FAILURE
- INCOMPLETE_LEARNING_PATH
- MISSED_ASSESSMENT
- PRACTICAL_EVIDENCE_GAP
- MULTI_FACTOR
"""

from decimal import Decimal
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.domains.institutional_intelligence.models import AcademicInterventionSignal
from app.domains.mastery.models import StudentConceptKnowledgeState, ConceptReviewState
from app.domains.assessment.models import AssessmentAttempt, AssessmentEvaluation, QuestionConcept
from app.domains.remediation.config import (
    ALGORITHM_VERSION,
    PRIORITY_WEIGHTS,
    MASTERY_PROFICIENCY_THRESHOLD,
    MASTERY_DEVELOPING_THRESHOLD,
    PREREQUISITE_READINESS_THRESHOLD,
    RETENTION_RISK_THRESHOLD,
)
from app.domains.remediation.prerequisite_path_engine import PrerequisitePathEngine


class DiagnosticEngine:
    """Deterministic, explainable academic diagnostic engine."""

    @staticmethod
    def calculate_priority_score(
        mastery_gap: Decimal,
        retention_risk: Decimal,
        prerequisite_block: Decimal,
        repeated_failure: Decimal,
        overdue_learning: Decimal,
        course_criticality: Decimal = Decimal("0.50"),
    ) -> Decimal:
        """Deterministic priority score formula:
        remediation_priority =
            0.30 * mastery_gap
          + 0.20 * retention_risk
          + 0.20 * prerequisite_block
          + 0.15 * repeated_failure
          + 0.10 * overdue_learning
          + 0.05 * course_criticality
        Clamped to [0.0000, 1.0000].
        """
        score = (
            PRIORITY_WEIGHTS["mastery_gap"] * mastery_gap
            + PRIORITY_WEIGHTS["retention_risk"] * retention_risk
            + PRIORITY_WEIGHTS["prerequisite_block"] * prerequisite_block
            + PRIORITY_WEIGHTS["repeated_failure"] * repeated_failure
            + PRIORITY_WEIGHTS["overdue_learning"] * overdue_learning
            + PRIORITY_WEIGHTS["course_criticality"] * course_criticality
        )
        return max(Decimal("0.0000"), min(Decimal("1.0000"), score.quantize(Decimal("0.0001"))))

    @staticmethod
    async def diagnose_deficiency(
        db: AsyncSession,
        student_profile_id: str,
        target_concept_id: str,
        originating_signal: Optional[AcademicInterventionSignal] = None,
    ) -> Dict[str, Any]:
        """Synthesize explainable deterministic diagnosis from authoritative records."""
        # 1. Inspect student knowledge state for target concept
        stmt = select(StudentConceptKnowledgeState).where(
            StudentConceptKnowledgeState.student_profile_id == student_profile_id,
            StudentConceptKnowledgeState.concept_id == target_concept_id,
        )
        k_res = await db.execute(stmt)
        k_state = k_res.scalar_one_or_none()

        mastery_before = Decimal(str(k_state.current_mastery)) if (k_state and k_state.current_mastery is not None) else None
        confidence_before = Decimal(str(k_state.confidence)) if k_state else Decimal("0.0000")
        retention_before = Decimal(str(k_state.retention_estimate)) if k_state else Decimal("1.0000")
        evidence_count = k_state.evidence_count if k_state else 0

        # 2. Inspect review schedule (overdue spaced repetition)
        rev_stmt = select(ConceptReviewState).where(
            ConceptReviewState.student_profile_id == student_profile_id,
            ConceptReviewState.concept_id == target_concept_id,
        )
        rev_res = await db.execute(rev_stmt)
        rev_state = rev_res.scalar_one_or_none()
        overdue_reviews = rev_state.total_reviews if rev_state else 0

        # 3. Prerequisite DAG traversal
        prereq_analysis = await PrerequisitePathEngine.get_prerequisite_chain(
            db, target_concept_id=target_concept_id, student_profile_id=student_profile_id
        )
        prereq_blocking = len(prereq_analysis["blocking_prerequisites"]) > 0
        prereq_readiness = Decimal("0.0000") if prereq_blocking else Decimal("1.0000")

        # 4. Count assessment failures directly linked to this concept
        fail_stmt = (
            select(func.count(AssessmentAttempt.id))
            .select_from(AssessmentAttempt)
            .join(AssessmentEvaluation, AssessmentEvaluation.attempt_id == AssessmentAttempt.id)
            .join(QuestionConcept, QuestionConcept.question_version_id == AssessmentEvaluation.question_version_id)
            .where(
                AssessmentAttempt.student_profile_id == student_profile_id,
                QuestionConcept.concept_id == target_concept_id,
                AssessmentEvaluation.is_correct == False,
            )
        )
        fail_res = await db.execute(fail_stmt)
        failure_count = fail_res.scalar() or 0

        # Calculate normalized component metrics for priority
        m_val = mastery_before if mastery_before is not None else Decimal("0.0")
        mastery_gap = max(Decimal("0.0"), Decimal("1.0") - m_val)
        retention_risk = max(Decimal("0.0"), Decimal("1.0") - retention_before)
        prereq_block_weight = Decimal("1.0000") if prereq_blocking else Decimal("0.0000")
        repeated_fail_weight = min(Decimal("1.0"), Decimal(str(failure_count)) / Decimal("3.0"))
        overdue_weight = min(Decimal("1.0"), Decimal(str(overdue_reviews)) / Decimal("5.0"))

        priority_score = DiagnosticEngine.calculate_priority_score(
            mastery_gap=mastery_gap,
            retention_risk=retention_risk,
            prerequisite_block=prereq_block_weight,
            repeated_failure=repeated_fail_weight,
            overdue_learning=overdue_weight,
        )

        # Deterministic Diagnosis Classification
        diagnosis_category = "LOW_MASTERY"
        diagnosis_reasons = []

        if prereq_blocking:
            first_block = prereq_analysis["blocking_prerequisites"][0]["name"]
            diagnosis_category = "PREREQUISITE_GAP"
            diagnosis_reasons.append(f"Blocked by foundational prerequisite deficiency: {first_block}")

        if failure_count >= 2:
            if diagnosis_category == "PREREQUISITE_GAP":
                diagnosis_category = "MULTI_FACTOR"
            else:
                diagnosis_category = "REPEATED_ASSESSMENT_FAILURE"
            diagnosis_reasons.append(f"Observed {failure_count} recent incorrect assessment responses on concept items")

        if retention_before < RETENTION_RISK_THRESHOLD and (mastery_before and mastery_before >= MASTERY_DEVELOPING_THRESHOLD):
            if diagnosis_category != "MULTI_FACTOR":
                diagnosis_category = "LOW_RETENTION"
            diagnosis_reasons.append(f"Memory retention estimated at {float(retention_before):.2f}, indicating acute decay")

        if mastery_before is not None and mastery_before < MASTERY_DEVELOPING_THRESHOLD:
            diagnosis_reasons.append(f"Stable concept mastery is {float(mastery_before):.2f}, below proficiency threshold of {float(MASTERY_PROFICIENCY_THRESHOLD):.2f}")

        if not diagnosis_reasons:
            diagnosis_category = "LOW_MASTERY"
            diagnosis_reasons.append("Mastery score or assessment evidence below academic target")

        full_reason = "; ".join(diagnosis_reasons)

        explanation_payload = {
            "diagnosis_category": diagnosis_category,
            "mastery_before": float(mastery_before) if mastery_before is not None else None,
            "confidence_before": float(confidence_before),
            "retention_before": float(retention_before),
            "prerequisite_blocking_count": len(prereq_analysis["blocking_prerequisites"]),
            "blocking_prerequisites": [p["name"] for p in prereq_analysis["blocking_prerequisites"]],
            "failure_count": failure_count,
            "evidence_count": evidence_count,
            "algorithm_version": ALGORITHM_VERSION,
        }

        return {
            "diagnosis_category": diagnosis_category,
            "diagnosis_reason": full_reason,
            "priority_score": priority_score,
            "evidence_count": evidence_count,
            "mastery_before": mastery_before,
            "confidence_before": confidence_before,
            "retention_before": retention_before,
            "prerequisite_readiness": prereq_readiness,
            "failure_count": failure_count,
            "overdue_review_count": overdue_reviews,
            "explanation_payload": explanation_payload,
            "prereq_analysis": prereq_analysis,
        }
