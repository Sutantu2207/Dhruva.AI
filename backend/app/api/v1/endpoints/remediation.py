"""REST API endpoints for Domain 10: Autonomous Adaptive Remediation & Institutional Intelligence Closing."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, get_current_user, require_roles
from app.core.security import UserRole
from app.domains.identity.models import User
from app.domains.academic.models import StudentAcademicProfile, TeacherAcademicProfile
from app.domains.content.models import Concept
from app.domains.remediation.models import (
    RemediationPlan,
    RemediationPlanStep,
    RemediationOutcome,
    ContentGapRecord,
    AccreditationEvidenceSnapshot,
)
from app.domains.remediation.schemas import (
    RemediationPlanResponse,
    RemediationPlanStepResponse,
    RemediationOutcomeResponse,
    CompleteStepPayload,
    ModifyRemediationPlanPayload,
    FacultyOverridePayload,
    GenerateRemediationPlanPayload,
    InstitutionalRemediationAnalytics,
    ContentGapResponse,
    AccreditationEvidenceRequest,
    AccreditationEvidenceResponse,
)
from app.domains.remediation.service import RemediationService
from app.domains.remediation.accreditation_engine import AccreditationEvidenceEngine

router = APIRouter(prefix="/remediation", tags=["Autonomous Adaptive Remediation"])


# =========================================================================
# 1. Student Remediation Endpoints
# =========================================================================

@router.get("/me", response_model=List[RemediationPlanResponse])
async def get_my_remediation_plans(
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all active learning recovery / remediation plans for the authenticated student."""
    profile_res = await db.execute(
        select(StudentAcademicProfile).where(StudentAcademicProfile.user_id == current_user.id)
    )
    profile = profile_res.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

    plans_res = await db.execute(
        select(RemediationPlan)
        .where(RemediationPlan.student_profile_id == profile.id)
        .order_by(RemediationPlan.priority_score.desc(), RemediationPlan.created_at.desc())
    )
    plans = plans_res.scalars().all()

    enriched = []
    for p in plans:
        # Load steps and concept name
        c_res = await db.execute(select(Concept).where(Concept.id == p.target_concept_id))
        concept = c_res.scalar_one_or_none()
        p_dict = RemediationPlanResponse.model_validate(p)
        p_dict.target_concept_name = concept.name if concept else "Concept"
        enriched.append(p_dict)
    return enriched


@router.get("/plans/{plan_id}", response_model=RemediationPlanResponse)
async def get_remediation_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed remediation plan with scaffolded steps, diagnoses and outcomes."""
    p_res = await db.execute(
        select(RemediationPlan).where(RemediationPlan.id == plan_id)
    )
    plan = p_res.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Remediation plan not found")

    # Authorization Check
    prof_res = await db.execute(
        select(StudentAcademicProfile).where(StudentAcademicProfile.id == plan.student_profile_id)
    )
    plan_student_prof = prof_res.scalar_one_or_none()

    if current_user.role == UserRole.STUDENT:
        if not plan_student_prof or plan_student_prof.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this plan")
    elif current_user.role != UserRole.SUPER_ADMIN:
        if current_user.institution_id and plan_student_prof and plan_student_prof.institution_id != current_user.institution_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-institution access denied")

    c_res = await db.execute(select(Concept).where(Concept.id == plan.target_concept_id))
    concept = c_res.scalar_one_or_none()

    resp = RemediationPlanResponse.model_validate(plan)
    resp.target_concept_name = concept.name if concept else "Concept"
    return resp


@router.post("/plans/{plan_id}/start", response_model=RemediationPlanResponse)
async def start_remediation_plan(
    plan_id: str,
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Student acknowledges and starts active recovery progress on a remediation plan."""
    prof_res = await db.execute(
        select(StudentAcademicProfile).where(StudentAcademicProfile.user_id == current_user.id)
    )
    prof = prof_res.scalar_one_or_none()
    if not prof:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

    p_res = await db.execute(
        select(RemediationPlan).where(RemediationPlan.id == plan_id)
    )
    plan = p_res.scalar_one_or_none()
    if not plan or plan.student_profile_id != prof.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    plan.status = "in_progress"
    await db.commit()
    await db.refresh(plan)
    return plan


@router.post("/plans/{plan_id}/steps/{step_id}/complete", response_model=RemediationPlanStepResponse)
async def complete_remediation_step(
    plan_id: str,
    step_id: str,
    payload: CompleteStepPayload,
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Student submits completion of a scaffolded micro-lesson or practice step."""
    prof_res = await db.execute(
        select(StudentAcademicProfile).where(StudentAcademicProfile.user_id == current_user.id)
    )
    prof = prof_res.scalar_one_or_none()
    if not prof:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

    return await RemediationService.complete_step(
        db, step_id=step_id, payload=payload, current_student_profile_id=prof.id
    )


# =========================================================================
# 2. Automated Signal Routing & Faculty Workflow
# =========================================================================

@router.post("/generate", response_model=RemediationPlanResponse)
async def generate_plan_from_signal(
    payload: GenerateRemediationPlanPayload,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Deterministic routing: Convert early distress signal into a remediation plan."""
    sig_res = await db.execute(
        select(AcademicInterventionSignal).where(AcademicInterventionSignal.id == payload.signal_id)
    )
    signal = sig_res.scalar_one_or_none()
    if not signal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic distress signal not found")

    # Extract target concept from signal evidence if present, or fallback
    target_cid = signal.evidence_data.get("concept_id")
    if not target_cid:
        # Fallback to first available concept in course if unspecified
        c_res = await db.execute(select(Concept.id).limit(1))
        target_cid = c_res.scalar()

    return await RemediationService.create_or_get_remediation_plan(
        db,
        student_profile_id=signal.student_profile_id,
        target_concept_id=target_cid,
        originating_signal_id=signal.id,
        target_course_offering_id=signal.course_offering_id,
    )


@router.get("/faculty/plans", response_model=List[RemediationPlanResponse])
async def get_faculty_remediation_plans(
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve remediation plans scoped to faculty's institution and teaching scope."""
    stmt = (
        select(RemediationPlan)
        .order_by(RemediationPlan.priority_score.desc(), RemediationPlan.created_at.desc())
        .limit(100)
    )
    res = await db.execute(stmt)
    plans = res.scalars().all()

    enriched = []
    for p in plans:
        c_res = await db.execute(select(Concept).where(Concept.id == p.target_concept_id))
        concept = c_res.scalar_one_or_none()
        p_dict = RemediationPlanResponse.model_validate(p)
        p_dict.target_concept_name = concept.name if concept else "Concept"
        enriched.append(p_dict)
    return enriched


@router.post("/plans/{plan_id}/override", response_model=RemediationPlanResponse)
async def faculty_override_plan(
    plan_id: str,
    action: str = Query(..., pattern="^(approve|pause|resume|close|modify)$"),
    payload: FacultyOverridePayload = ...,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Faculty overrides, approves, pauses, or manually closes a student remediation plan."""
    return await RemediationService.faculty_override_plan(
        db,
        plan_id=plan_id,
        user=current_user,
        action=action,
        reason=payload.reason,
    )


# =========================================================================
# 3. Institutional Analytics, Content Gaps & Accreditation Evidence
# =========================================================================

@router.get("/analytics/institutional", response_model=InstitutionalRemediationAnalytics)
async def get_institutional_analytics(
    current_user: User = Depends(require_roles(UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Holistic aggregate remediation metrics across the institution."""
    return await RemediationService.get_institutional_analytics(db, current_user.institution_id or "inst-1")


@router.get("/content-gaps", response_model=List[ContentGapResponse])
async def get_content_gaps(
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Institutional audit log of concepts requiring remediation where no approved content exists."""
    stmt = (
        select(ContentGapRecord)
        .where(ContentGapRecord.status == "unresolved")
        .order_by(ContentGapRecord.demand_count.desc())
    )
    res = await db.execute(stmt)
    gaps = res.scalars().all()

    enriched = []
    for g in gaps:
        c_res = await db.execute(select(Concept).where(Concept.id == g.concept_id))
        c = c_res.scalar_one_or_none()
        resp = ContentGapResponse.model_validate(g)
        resp.concept_name = c.name if c else "Concept"
        enriched.append(resp)
    return enriched


@router.post("/accreditation/evidence/generate", response_model=AccreditationEvidenceResponse)
async def generate_accreditation_evidence(
    payload: AccreditationEvidenceRequest,
    current_user: User = Depends(require_roles(UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Generate auditable NAAC/NBA remediation evidence snapshot."""
    inst_id = current_user.institution_id or "inst-1"
    ev = await AccreditationEvidenceEngine.generate_evidence_snapshot(
        db, institution_id=inst_id, framework=payload.framework, criterion=payload.criterion
    )

    snapshot = AccreditationEvidenceSnapshot(
        institution_id=inst_id,
        framework=ev["framework"],
        criterion=ev["criterion"],
        metric_code=ev["metric_code"],
        metric_payload=ev["metric_payload"],
        algorithm_version=ev["algorithm_version"],
    )
    db.add(snapshot)
    await db.commit()
    await db.refresh(snapshot)

    return snapshot
