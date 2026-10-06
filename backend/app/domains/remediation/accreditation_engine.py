"""Accreditation Evidence Engine for Domain 10 (NAAC / NBA Preparation).

Maps observable remediation activity, improvement outcomes, and curriculum gap findings
to standard accreditation criteria (e.g., NAAC Criteria 2: Teaching-Learning & Evaluation,
NBA Criterion 3: Course Outcomes & Program Outcomes).

CRITICAL INVARIANT: Prepares auditable evidence snapshots only.
Never asserts legal or official accreditation compliance.
"""

from typing import Dict, Any, List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.domains.remediation.models import RemediationPlan, RemediationOutcome, ContentGapRecord
from app.domains.remediation.config import ALGORITHM_VERSION


class AccreditationEvidenceEngine:
    """Deterministic evidence preparation engine for institutional accreditation audits."""

    @staticmethod
    async def generate_evidence_snapshot(
        db: AsyncSession,
        institution_id: str,
        framework: str,  # NAAC, NBA, NIRF, ABET
        criterion: str,
    ) -> Dict[str, Any]:
        """Synthesizes auditable aggregate data mapping to specified framework criterion."""
        # 1. Total remediation plans created & completed in institution
        p_stmt = (
            select(
                func.count(RemediationPlan.id).label("total_plans"),
                func.count().filter(RemediationPlan.status == "completed").label("completed_plans"),
                func.count().filter(RemediationPlan.status == "closed").label("closed_plans"),
            )
            .join(RemediationPlan.student_profile)
            .where(RemediationPlan.student_profile.has(institution_id=institution_id))
        )
        p_res = await db.execute(p_stmt)
        p_row = p_res.first()
        total_plans = p_row.total_plans if p_row else 0
        completed_plans = p_row.completed_plans if p_row else 0
        closed_plans = p_row.closed_plans if p_row else 0

        # 2. Count measured outcomes
        o_stmt = (
            select(
                func.count(RemediationOutcome.id).label("total_outcomes"),
                func.count().filter(RemediationOutcome.outcome_status == "IMPROVED").label("improved_count"),
                func.count().filter(RemediationOutcome.outcome_status == "PARTIALLY_IMPROVED").label("partial_count"),
                func.avg(RemediationOutcome.improvement_delta).label("avg_delta"),
            )
            .join(RemediationOutcome.remediation_plan)
            .join(RemediationPlan.student_profile)
            .where(RemediationPlan.student_profile.has(institution_id=institution_id))
        )
        o_res = await db.execute(o_stmt)
        o_row = o_res.first()
        total_outcomes = o_row.total_outcomes if o_row else 0
        improved_count = o_row.improved_count if o_row else 0
        partial_count = o_row.partial_count if o_row else 0
        avg_delta = Decimal(str(o_row.avg_delta)) if (o_row and o_row.avg_delta is not None) else Decimal("0.0000")

        # 3. Content gaps recorded
        g_stmt = (
            select(func.count(ContentGapRecord.id))
            .where(ContentGapRecord.institution_id == institution_id)
        )
        g_res = await db.execute(g_stmt)
        gap_count = g_res.scalar() or 0

        # Build auditable evidence payload
        evidence_payload = {
            "framework": framework,
            "criterion": criterion,
            "metric_title": (
                "Remediation & Slow Learner Support (Teaching-Learning Process)"
                if framework == "NAAC"
                else "Course Outcome Attainment & Remedial Actions"
            ),
            "evidence_indicators": {
                "total_remediation_interventions": total_plans,
                "successfully_completed_interventions": completed_plans + closed_plans,
                "completion_rate": float(
                    (Decimal(str(completed_plans + closed_plans)) / Decimal(str(total_plans))).quantize(Decimal("0.0001"))
                ) if total_plans > 0 else 0.0,
                "documented_learning_improvements": improved_count + partial_count,
                "improvement_success_rate": float(
                    (Decimal(str(improved_count + partial_count)) / Decimal(str(total_outcomes))).quantize(Decimal("0.0001"))
                ) if total_outcomes > 0 else 0.0,
                "average_mastery_gain": float(avg_delta.quantize(Decimal("0.0001"))),
                "unresolved_curriculum_content_gaps": gap_count,
            },
            "compliance_claim": "Evidence mapped to configured accreditation criterion. Not an official compliance claim.",
            "algorithm_version": ALGORITHM_VERSION,
        }

        metric_code = f"{framework}_{criterion.replace('.', '_')}_REMEDIAL_ACTION"

        return {
            "framework": framework,
            "criterion": criterion,
            "metric_code": metric_code,
            "metric_payload": evidence_payload,
            "algorithm_version": ALGORITHM_VERSION,
        }
