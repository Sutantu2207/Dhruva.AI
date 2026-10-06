"""Domain 10 Remediation Service.

Orchestrates:
- Idempotent plan generation from signals or direct diagnosis
- Step execution and attempt tracking
- Reassessment submission & outcome measurement
- Faculty plan approval, overrides, and closure
- Institutional analytics & Content gap logging
- NAAC / NBA evidence snapshot generation
"""

import hashlib
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status

from app.domains.identity.models import User
from app.domains.academic.models import StudentAcademicProfile, CourseOffering, Course
from app.domains.content.models import Concept
from app.domains.institutional_intelligence.models import AcademicInterventionSignal
from app.domains.mastery.models import StudentConceptKnowledgeState
from app.domains.remediation.models import (
    RemediationPlan,
    RemediationPlanStep,
    RemediationDiagnosis,
    RemediationAttempt,
    RemediationOutcome,
    ContentGapRecord,
    AccreditationEvidenceSnapshot,
)
from app.domains.remediation.config import ALGORITHM_VERSION, MASTERY_PROFICIENCY_THRESHOLD
from app.domains.remediation.diagnostic_engine import DiagnosticEngine
from app.domains.remediation.remediation_engine import RemediationEngine
from app.domains.remediation.outcome_engine import OutcomeEngine
from app.domains.remediation.accreditation_engine import AccreditationEvidenceEngine
from app.domains.remediation.schemas import (
    CompleteStepPayload,
    ModifyRemediationPlanPayload,
    InstitutionalRemediationAnalytics,
    DepartmentRemediationAnalytics,
)


class RemediationService:
    """Core domain service for closed-loop adaptive remediation."""

    @staticmethod
    def generate_idempotency_key(
        student_profile_id: str,
        signal_type: str,
        target_concept_id: str,
        version: str = ALGORITHM_VERSION,
    ) -> str:
        """Deterministic SHA256 key preventing duplicate active remediation plans."""
        raw = f"{student_profile_id}:{signal_type}:{target_concept_id}:{version}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    async def create_or_get_remediation_plan(
        db: AsyncSession,
        student_profile_id: str,
        target_concept_id: str,
        originating_signal_id: Optional[str] = None,
        originating_intervention_id: Optional[str] = None,
        target_course_offering_id: Optional[str] = None,
    ) -> RemediationPlan:
        """Create a new remediation plan or return existing active plan idempotently."""
        # Check student profile
        s_res = await db.execute(
            select(StudentAcademicProfile).where(StudentAcademicProfile.id == student_profile_id)
        )
        student_profile = s_res.scalar_one_or_none()
        if not student_profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student academic profile not found")

        # Check concept
        c_res = await db.execute(select(Concept).where(Concept.id == target_concept_id))
        target_concept = c_res.scalar_one_or_none()
        if not target_concept:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target concept not found")

        signal: Optional[AcademicInterventionSignal] = None
        signal_type = "ACADEMIC_DEFICIENCY"
        if originating_signal_id:
            sig_res = await db.execute(
                select(AcademicInterventionSignal).where(AcademicInterventionSignal.id == originating_signal_id)
            )
            signal = sig_res.scalar_one_or_none()
            if signal:
                signal_type = signal.signal_type
                if not target_course_offering_id:
                    target_course_offering_id = signal.course_offering_id

        idempotency_key = RemediationService.generate_idempotency_key(
            student_profile_id, signal_type, target_concept_id, ALGORITHM_VERSION
        )

        # Check for existing active plan with this key
        existing_stmt = select(RemediationPlan).where(
            RemediationPlan.idempotency_key == idempotency_key,
            RemediationPlan.status.in_(["draft", "recommended", "assigned", "in_progress", "paused"]),
        )
        existing_res = await db.execute(existing_stmt)
        existing_plan = existing_res.scalar_one_or_none()
        if existing_plan:
            return existing_plan

        # 1. Run Diagnostic Engine
        diagnosis_info = await DiagnosticEngine.diagnose_deficiency(
            db, student_profile_id, target_concept_id, originating_signal=signal
        )

        # 2. Synthesize Steps via Remediation Engine
        steps_data = await RemediationEngine.synthesize_plan_steps(
            db, target_concept_id, diagnosis_info
        )

        # 3. Persist Remediation Plan
        plan = RemediationPlan(
            student_profile_id=student_profile_id,
            originating_signal_id=originating_signal_id,
            originating_intervention_id=originating_intervention_id,
            target_concept_id=target_concept_id,
            target_course_offering_id=target_course_offering_id,
            diagnosis_type=diagnosis_info["diagnosis_category"],
            diagnosis_reason=diagnosis_info["diagnosis_reason"],
            priority_score=diagnosis_info["priority_score"],
            status="recommended",
            idempotency_key=idempotency_key,
            algorithm_version=ALGORITHM_VERSION,
        )
        db.add(plan)
        await db.flush()

        # 4. Persist Diagnosis Record
        diagnosis = RemediationDiagnosis(
            remediation_plan_id=plan.id,
            concept_id=target_concept_id,
            evidence_count=diagnosis_info["evidence_count"],
            mastery_before=diagnosis_info["mastery_before"],
            confidence_before=diagnosis_info["confidence_before"],
            retention_before=diagnosis_info["retention_before"],
            prerequisite_readiness=diagnosis_info["prerequisite_readiness"],
            failure_count=diagnosis_info["failure_count"],
            overdue_review_count=diagnosis_info["overdue_review_count"],
            diagnosis_category=diagnosis_info["diagnosis_category"],
            diagnosis_reason=diagnosis_info["diagnosis_reason"],
            explanation_payload=diagnosis_info["explanation_payload"],
            algorithm_version=ALGORITHM_VERSION,
        )
        db.add(diagnosis)

        # 5. Persist Steps & Audit Content Gaps
        for s in steps_data:
            step = RemediationPlanStep(
                remediation_plan_id=plan.id,
                sequence_order=s["sequence_order"],
                step_type=s["step_type"],
                concept_id=s.get("concept_id"),
                lesson_id=s.get("lesson_id"),
                resource_id=s.get("resource_id"),
                assessment_id=s.get("assessment_id"),
                title=s["title"],
                description=s.get("description"),
                required=s.get("required", True),
                scaffold_level=s.get("scaffold_level", 1),
                completion_status="pending",
            )
            db.add(step)

            # Detect content gap if lesson or assessment was not available
            if s["step_type"] in ["PREREQUISITE", "MICRO_LESSON"] and not s.get("lesson_id") and not s.get("resource_id"):
                await RemediationService._log_content_gap(
                    db,
                    institution_id=student_profile.institution_id,
                    concept_id=s.get("concept_id") or target_concept_id,
                    course_offering_id=target_course_offering_id,
                    gap_type="NO_APPROVED_LESSON",
                )
            elif s["step_type"] == "REASSESSMENT" and not s.get("assessment_id"):
                await RemediationService._log_content_gap(
                    db,
                    institution_id=student_profile.institution_id,
                    concept_id=target_concept_id,
                    course_offering_id=target_course_offering_id,
                    gap_type="NO_REASSESSMENT",
                )

        await db.commit()
        await db.refresh(plan)
        return plan

    @staticmethod
    async def _log_content_gap(
        db: AsyncSession,
        institution_id: str,
        concept_id: str,
        course_offering_id: Optional[str],
        gap_type: str,
    ) -> None:
        """Record or increment demand count on an institutional content gap."""
        course_id = None
        if course_offering_id:
            co_res = await db.execute(
                select(CourseOffering).where(CourseOffering.id == course_offering_id)
            )
            co = co_res.scalar_one_or_none()
            if co:
                course_id = co.course_id

        stmt = select(ContentGapRecord).where(
            ContentGapRecord.institution_id == institution_id,
            ContentGapRecord.concept_id == concept_id,
        )
        res = await db.execute(stmt)
        gap = res.scalar_one_or_none()
        if gap:
            gap.demand_count += 1
            gap.gap_type = gap_type
        else:
            gap = ContentGapRecord(
                institution_id=institution_id,
                concept_id=concept_id,
                course_id=course_id,
                demand_count=1,
                gap_type=gap_type,
                status="unresolved",
            )
            db.add(gap)
        await db.flush()

    @staticmethod
    async def complete_step(
        db: AsyncSession,
        step_id: str,
        payload: CompleteStepPayload,
        current_student_profile_id: str,
    ) -> RemediationPlanStep:
        """Student marks a remediation step completed, logging a deterministic attempt."""
        s_res = await db.execute(
            select(RemediationPlanStep).where(RemediationPlanStep.id == step_id)
        )
        step = s_res.scalar_one_or_none()
        if not step:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Remediation plan step not found")

        plan_res = await db.execute(
            select(RemediationPlan).where(RemediationPlan.id == step.remediation_plan_id)
        )
        plan = plan_res.scalar_one_or_none()
        if not plan or plan.student_profile_id != current_student_profile_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this remediation step")

        # Determine attempt number
        att_cnt_res = await db.execute(
            select(func.count(RemediationAttempt.id)).where(RemediationAttempt.remediation_plan_step_id == step.id)
        )
        attempt_num = (att_cnt_res.scalar() or 0) + 1

        now = datetime.now(timezone.utc)
        attempt = RemediationAttempt(
            remediation_plan_step_id=step.id,
            student_profile_id=current_student_profile_id,
            attempt_number=attempt_num,
            started_at=step.started_at or now,
            submitted_at=now,
            score=payload.score,
            completion_percentage=payload.completion_percentage,
            outcome="passed" if (payload.score is None or payload.score >= Decimal("50.0")) else "failed",
            evidence_generated=payload.evidence_generated,
        )
        db.add(attempt)

        step.completion_status = "completed"
        step.completed_at = now
        step.result_summary = {
            "attempt_number": attempt_num,
            "score": float(payload.score) if payload.score is not None else None,
            "completion_percentage": float(payload.completion_percentage),
            "evidence": payload.evidence_generated,
        }

        # Progress plan status if needed
        if plan.status in ["recommended", "assigned"]:
            plan.status = "in_progress"
            plan.started_at = now

        # If all steps completed, evaluate outcome
        all_steps_res = await db.execute(
            select(RemediationPlanStep).where(RemediationPlanStep.remediation_plan_id == plan.id)
        )
        all_steps = all_steps_res.scalars().all()
        if all(s.completion_status == "completed" for s in all_steps):
            plan.status = "completed"
            plan.completed_at = now
            # Run closed-loop outcome evaluation
            await RemediationService.evaluate_and_close_plan(db, plan)

        await db.commit()
        await db.refresh(step)
        return step

    @staticmethod
    async def evaluate_and_close_plan(
        db: AsyncSession, plan: RemediationPlan
    ) -> RemediationOutcome:
        """Execute closed loop outcome evaluation comparing BEFORE and AFTER states."""
        # 1. Fetch initial diagnosis
        diag_res = await db.execute(
            select(RemediationDiagnosis).where(RemediationDiagnosis.remediation_plan_id == plan.id)
        )
        diagnosis = diag_res.scalars().first()

        # 2. Fetch current post-remediation knowledge state from Domain 6
        k_res = await db.execute(
            select(StudentConceptKnowledgeState).where(
                StudentConceptKnowledgeState.student_profile_id == plan.student_profile_id,
                StudentConceptKnowledgeState.concept_id == plan.target_concept_id,
            )
        )
        k_state = k_res.scalar_one_or_none()

        mastery_after = Decimal(str(k_state.current_mastery)) if (k_state and k_state.current_mastery is not None) else None
        confidence_after = Decimal(str(k_state.confidence)) if k_state else Decimal("0.0000")
        retention_after = Decimal(str(k_state.retention_estimate)) if k_state else Decimal("1.0000")

        mastery_before = diagnosis.mastery_before if diagnosis else None
        confidence_before = diagnosis.confidence_before if diagnosis else Decimal("0.0000")
        retention_before = diagnosis.retention_before if diagnosis else Decimal("1.0000")

        outcome_result = OutcomeEngine.evaluate_outcome(
            mastery_before=mastery_before,
            mastery_after=mastery_after,
            confidence_before=confidence_before,
            confidence_after=confidence_after,
            retention_before=retention_before,
            retention_after=retention_after,
            prerequisite_blocking=False,
        )

        outcome = RemediationOutcome(
            remediation_plan_id=plan.id,
            concept_id=plan.target_concept_id,
            mastery_before=mastery_before,
            confidence_before=confidence_before,
            retention_before=retention_before,
            mastery_after=mastery_after,
            confidence_after=confidence_after,
            retention_after=retention_after,
            improvement_delta=outcome_result["improvement_delta"],
            outcome_status=outcome_result["outcome_status"],
            closure_decision=outcome_result["closure_decision"],
            closure_reason=outcome_result["closure_reason"],
            algorithm_version=ALGORITHM_VERSION,
        )
        db.add(outcome)

        if outcome_result["closure_decision"] == "CLOSE_SUCCESS":
            plan.status = "closed"
            plan.closed_at = datetime.now(timezone.utc)

        await db.flush()
        return outcome

    @staticmethod
    async def faculty_override_plan(
        db: AsyncSession,
        plan_id: str,
        user: User,
        action: str,  # approve, pause, resume, close, modify
        reason: str,
        modify_payload: Optional[ModifyRemediationPlanPayload] = None,
    ) -> RemediationPlan:
        """Authorized faculty modifications and overrides to remediation plans."""
        p_res = await db.execute(
            select(RemediationPlan).where(RemediationPlan.id == plan_id)
        )
        plan = p_res.scalar_one_or_none()
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Remediation plan not found")

        plan.faculty_reviewer_id = user.id
        plan.faculty_override_reason = f"[{action.upper()}] {reason}"

        if action == "approve":
            plan.status = "assigned"
        elif action == "pause":
            plan.status = "paused"
        elif action == "resume":
            plan.status = "in_progress"
        elif action == "close":
            plan.status = "closed"
            plan.closed_at = datetime.now(timezone.utc)
        elif action == "modify" and modify_payload:
            if modify_payload.remove_step_ids:
                del_stmt = select(RemediationPlanStep).where(
                    RemediationPlanStep.id.in_(modify_payload.remove_step_ids),
                    RemediationPlanStep.remediation_plan_id == plan.id,
                )
                del_res = await db.execute(del_stmt)
                for s in del_res.scalars().all():
                    await db.delete(s)

            if modify_payload.added_steps:
                for added in modify_payload.added_steps:
                    new_step = RemediationPlanStep(
                        remediation_plan_id=plan.id,
                        sequence_order=added.sequence_order,
                        step_type=added.step_type,
                        concept_id=added.concept_id,
                        lesson_id=added.lesson_id,
                        resource_id=added.resource_id,
                        assessment_id=added.assessment_id,
                        title=added.title,
                        description=added.description,
                        required=added.required,
                        scaffold_level=added.scaffold_level,
                        completion_status="pending",
                    )
                    db.add(new_step)

        await db.commit()
        await db.refresh(plan)
        return plan

    @staticmethod
    async def get_institutional_analytics(
        db: AsyncSession, institution_id: str
    ) -> InstitutionalRemediationAnalytics:
        """Synthesize institutional remediation performance metrics."""
        # Query total plans
        p_stmt = (
            select(
                func.count(RemediationPlan.id).label("total"),
                func.count().filter(RemediationPlan.status == "completed").label("completed"),
                func.count().filter(RemediationPlan.status == "closed").label("closed"),
            )
            .join(RemediationPlan.student_profile)
            .where(RemediationPlan.student_profile.has(institution_id=institution_id))
        )
        p_res = await db.execute(p_stmt)
        p_row = p_res.first()
        total_plans = p_row.total if p_row else 0
        completed_plans = p_row.completed if p_row else 0
        closed_plans = p_row.closed if p_row else 0

        # Query outcomes
        o_stmt = (
            select(
                func.count(RemediationOutcome.id).label("total_outcomes"),
                func.count().filter(RemediationOutcome.outcome_status == "IMPROVED").label("improved"),
                func.count().filter(RemediationOutcome.outcome_status == "PARTIALLY_IMPROVED").label("partial"),
                func.count().filter(RemediationOutcome.outcome_status == "NO_SIGNIFICANT_CHANGE").label("no_change"),
                func.count().filter(RemediationOutcome.outcome_status == "REGRESSED").label("regressed"),
                func.avg(RemediationOutcome.improvement_delta).label("avg_delta"),
            )
            .join(RemediationOutcome.remediation_plan)
            .join(RemediationPlan.student_profile)
            .where(RemediationPlan.student_profile.has(institution_id=institution_id))
        )
        o_res = await db.execute(o_stmt)
        o_row = o_res.first()
        tot_outcomes = o_row.total_outcomes if o_row else 0
        improved = o_row.improved if o_row else 0
        partial = o_row.partial if o_row else 0
        no_change = o_row.no_change if o_row else 0
        regressed = o_row.regressed if o_row else 0
        avg_delta = Decimal(str(o_row.avg_delta)) if (o_row and o_row.avg_delta is not None) else Decimal("0.0000")

        # Query top concepts demand
        c_stmt = (
            select(Concept.name, func.count(RemediationPlan.id).label("count"))
            .join(RemediationPlan, RemediationPlan.target_concept_id == Concept.id)
            .join(RemediationPlan.student_profile)
            .where(RemediationPlan.student_profile.has(institution_id=institution_id))
            .group_by(Concept.name)
            .order_by(func.count(RemediationPlan.id).desc())
            .limit(5)
        )
        c_res = await db.execute(c_stmt)
        concepts_highest = [{"name": row.name, "count": row.count} for row in c_res.all()]

        # Query content gaps
        gap_stmt = select(func.count(ContentGapRecord.id)).where(ContentGapRecord.institution_id == institution_id)
        gap_res = await db.execute(gap_stmt)
        gap_count = gap_res.scalar() or 0

        completion_rate = (
            (Decimal(str(completed_plans + closed_plans)) / Decimal(str(total_plans))).quantize(Decimal("0.0001"))
            if total_plans > 0 else Decimal("0.0000")
        )

        return InstitutionalRemediationAnalytics(
            plans_created=total_plans,
            plans_completed=completed_plans + closed_plans,
            completion_rate=completion_rate,
            improvement_rate=(
                (Decimal(str(improved)) / Decimal(str(tot_outcomes))).quantize(Decimal("0.0001"))
                if tot_outcomes > 0 else Decimal("0.0000")
            ),
            partial_improvement_rate=(
                (Decimal(str(partial)) / Decimal(str(tot_outcomes))).quantize(Decimal("0.0001"))
                if tot_outcomes > 0 else Decimal("0.0000")
            ),
            no_significant_change_rate=(
                (Decimal(str(no_change)) / Decimal(str(tot_outcomes))).quantize(Decimal("0.0001"))
                if tot_outcomes > 0 else Decimal("0.0000")
            ),
            regression_rate=(
                (Decimal(str(regressed)) / Decimal(str(tot_outcomes))).quantize(Decimal("0.0001"))
                if tot_outcomes > 0 else Decimal("0.0000")
            ),
            average_mastery_improvement=avg_delta.quantize(Decimal("0.0001")),
            prerequisite_bottlenecks=[],
            concepts_highest_demand=concepts_highest,
            courses_highest_demand=[],
            content_availability_gaps=gap_count,
            closure_rate=(
                (Decimal(str(closed_plans)) / Decimal(str(total_plans))).quantize(Decimal("0.0001"))
                if total_plans > 0 else Decimal("0.0000")
            ),
            algorithm_version=ALGORITHM_VERSION,
        )
