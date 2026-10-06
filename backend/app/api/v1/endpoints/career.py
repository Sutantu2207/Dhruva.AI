"""REST Endpoints for Domain 7: Skill Intelligence, Career Trajectories & Placement Readiness."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.api.deps import get_db, get_current_user, require_roles
from app.core.security import UserRole
from app.domains.identity.models import User
from app.domains.academic.models import StudentAcademicProfile
from app.domains.catalog.models import SkillCatalog, CareerCatalog
from app.domains.career_intelligence.models import (
    StudentSkillIntelligenceState,
    StudentSkillEvidenceRecord,
    StudentCareerReadinessState,
    CareerTrajectory,
)
from app.domains.career_intelligence.service import career_intelligence_service
from app.domains.career_intelligence.schemas import (
    SkillIntelligenceResponse,
    SkillDetailResponse,
    SkillGapResponse,
    CareerReadinessResponse,
    CareerTrajectoryResponse,
    CareerTrajectoryStepResponse,
    CareerComparisonItemResponse,
    PlacementReadinessResponse,
    CareerIntelligenceOverviewResponse,
)

router = APIRouter()


async def _resolve_student_profile(db: AsyncSession, user_id: str) -> StudentAcademicProfile:
    """Helper to resolve the student academic profile for the authenticated user."""
    stmt = select(StudentAcademicProfile).where(StudentAcademicProfile.user_id == user_id)
    res = await db.execute(stmt)
    prof = res.scalar_one_or_none()
    if not prof:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student academic profile not provisioned.",
        )
    return prof


# =========================================================================
# 1. Career Intelligence Overview & Readiness
# =========================================================================

@router.get("/career/intelligence", response_model=CareerIntelligenceOverviewResponse)
async def get_my_career_intelligence(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Returns authoritative student career intelligence synthesized from verified evidence."""
    prof = await _resolve_student_profile(db, current_user.id)

    # 1. Career Readiness
    c_state, calc_res = await career_intelligence_service.evaluate_career_readiness(db, prof.id)

    readiness_dto = CareerReadinessResponse(
        career_id=calc_res.career_id,
        career_title=calc_res.career_title,
        readiness_score=float(calc_res.readiness_score),
        fit_score=float(calc_res.fit_score),
        confidence=float(calc_res.confidence),
        required_skill_coverage=float(calc_res.required_skill_coverage),
        preferred_skill_coverage=float(calc_res.preferred_skill_coverage),
        critical_skill_coverage=float(calc_res.critical_skill_coverage),
        critical_gaps_count=len(calc_res.critical_gaps),
        strengths_count=len(calc_res.strengths),
        developing_count=len(calc_res.developing),
        status=calc_res.status,
        explanation=calc_res.explanation,
        critical_gaps=[
            SkillGapResponse(
                skill_id=g.skill_id,
                skill_name=g.skill_name,
                importance=g.importance,
                current_proficiency=float(g.current_proficiency),
                required_proficiency=float(g.required_proficiency),
                gap_size=float(g.gap_size),
                severity=g.severity,
                reason=g.reason,
            )
            for g in calc_res.critical_gaps
        ],
        strengths=[
            SkillGapResponse(
                skill_id=g.skill_id,
                skill_name=g.skill_name,
                importance=g.importance,
                current_proficiency=float(g.current_proficiency),
                required_proficiency=float(g.required_proficiency),
                gap_size=float(g.gap_size),
                severity=g.severity,
                reason=g.reason,
            )
            for g in calc_res.strengths
        ],
        developing=[
            SkillGapResponse(
                skill_id=g.skill_id,
                skill_name=g.skill_name,
                importance=g.importance,
                current_proficiency=float(g.current_proficiency),
                required_proficiency=float(g.required_proficiency),
                gap_size=float(g.gap_size),
                severity=g.severity,
                reason=g.reason,
            )
            for g in calc_res.developing
        ],
        algorithm_version=calc_res.algorithm_version,
    )

    # 2. Trajectory
    traj = await career_intelligence_service.generate_career_trajectory(db, prof.id, c_state.career_id)
    traj_dto = CareerTrajectoryResponse(
        career_id=traj.career_id,
        career_title=calc_res.career_title,
        status=traj.status,
        total_steps=traj.total_steps,
        completed_steps=traj.completed_steps,
        steps=[
            CareerTrajectoryStepResponse(
                step_number=s.step_number,
                skill_id=s.skill_id,
                title=s.title,
                step_type=s.step_type,
                priority=s.priority,
                status=s.status,
                target_proficiency=float(s.target_proficiency),
                current_proficiency=float(s.current_proficiency),
                gap_size=float(s.gap_size),
                reference_course_id=s.reference_course_id,
                reference_lesson_id=s.reference_lesson_id,
                reference_concept_id=s.reference_concept_id,
                reference_assessment_id=s.reference_assessment_id,
            )
            for s in traj.steps
        ],
        algorithm_version=traj.algorithm_version,
    )

    # 3. Placement Readiness
    p_state = await career_intelligence_service.evaluate_placement_readiness(db, prof.id)
    placement_dto = PlacementReadinessResponse(
        technical_readiness=float(p_state.technical_readiness) if p_state.technical_readiness is not None else None,
        assessment_readiness=float(p_state.assessment_readiness) if p_state.assessment_readiness is not None else None,
        project_evidence_score=float(p_state.project_evidence_score) if p_state.project_evidence_score is not None else None,
        communication_readiness=float(p_state.communication_readiness) if p_state.communication_readiness is not None else None,
        resume_readiness=float(p_state.resume_readiness) if p_state.resume_readiness is not None else None,
        interview_readiness=float(p_state.interview_readiness) if p_state.interview_readiness is not None else None,
        career_alignment=float(p_state.career_alignment) if p_state.career_alignment is not None else None,
        overall_status=p_state.overall_status,
        component_statuses=p_state.component_statuses,
        algorithm_version=p_state.algorithm_version,
    )

    # Skill counts
    skills_stmt = select(StudentSkillIntelligenceState).where(
        StudentSkillIntelligenceState.student_profile_id == prof.id
    )
    all_skills = (await db.execute(skills_stmt)).scalars().all()
    verified_count = sum(1 for s in all_skills if s.verification_status in ["verified", "certified"])

    return CareerIntelligenceOverviewResponse(
        target_career=readiness_dto,
        readiness=readiness_dto,
        trajectory=traj_dto,
        placement=placement_dto,
        total_skills_tracked=len(all_skills),
        verified_skills_count=verified_count,
        algorithm_version=calc_res.algorithm_version,
    )


@router.get("/career/readiness", response_model=CareerReadinessResponse)
async def get_my_career_readiness(
    career_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Returns deterministic career readiness and skill gap breakdown for target or specified career."""
    prof = await _resolve_student_profile(db, current_user.id)
    _, calc_res = await career_intelligence_service.evaluate_career_readiness(db, prof.id, career_id)

    return CareerReadinessResponse(
        career_id=calc_res.career_id,
        career_title=calc_res.career_title,
        readiness_score=float(calc_res.readiness_score),
        fit_score=float(calc_res.fit_score),
        confidence=float(calc_res.confidence),
        required_skill_coverage=float(calc_res.required_skill_coverage),
        preferred_skill_coverage=float(calc_res.preferred_skill_coverage),
        critical_skill_coverage=float(calc_res.critical_skill_coverage),
        critical_gaps_count=len(calc_res.critical_gaps),
        strengths_count=len(calc_res.strengths),
        developing_count=len(calc_res.developing),
        status=calc_res.status,
        explanation=calc_res.explanation,
        critical_gaps=[
            SkillGapResponse(
                skill_id=g.skill_id,
                skill_name=g.skill_name,
                importance=g.importance,
                current_proficiency=float(g.current_proficiency),
                required_proficiency=float(g.required_proficiency),
                gap_size=float(g.gap_size),
                severity=g.severity,
                reason=g.reason,
            )
            for g in calc_res.critical_gaps
        ],
        strengths=[
            SkillGapResponse(
                skill_id=g.skill_id,
                skill_name=g.skill_name,
                importance=g.importance,
                current_proficiency=float(g.current_proficiency),
                required_proficiency=float(g.required_proficiency),
                gap_size=float(g.gap_size),
                severity=g.severity,
                reason=g.reason,
            )
            for g in calc_res.strengths
        ],
        developing=[
            SkillGapResponse(
                skill_id=g.skill_id,
                skill_name=g.skill_name,
                importance=g.importance,
                current_proficiency=float(g.current_proficiency),
                required_proficiency=float(g.required_proficiency),
                gap_size=float(g.gap_size),
                severity=g.severity,
                reason=g.reason,
            )
            for g in calc_res.developing
        ],
        algorithm_version=calc_res.algorithm_version,
    )


@router.get("/career/trajectory", response_model=CareerTrajectoryResponse)
async def get_my_career_trajectory(
    career_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Returns the deterministic career trajectory sequencing learning milestones from skill gaps."""
    prof = await _resolve_student_profile(db, current_user.id)
    traj = await career_intelligence_service.generate_career_trajectory(db, prof.id, career_id)

    # Load career title
    c_title = "Career Pathway"
    if traj.career_id:
        c_obj = (await db.execute(select(CareerCatalog).where(CareerCatalog.id == traj.career_id))).scalar_one_or_none()
        if c_obj:
            c_title = c_obj.title

    return CareerTrajectoryResponse(
        career_id=traj.career_id,
        career_title=c_title,
        status=traj.status,
        total_steps=traj.total_steps,
        completed_steps=traj.completed_steps,
        steps=[
            CareerTrajectoryStepResponse(
                step_number=s.step_number,
                skill_id=s.skill_id,
                title=s.title,
                step_type=s.step_type,
                priority=s.priority,
                status=s.status,
                target_proficiency=float(s.target_proficiency),
                current_proficiency=float(s.current_proficiency),
                gap_size=float(s.gap_size),
                reference_course_id=s.reference_course_id,
                reference_lesson_id=s.reference_lesson_id,
                reference_concept_id=s.reference_concept_id,
                reference_assessment_id=s.reference_assessment_id,
            )
            for s in traj.steps
        ],
        algorithm_version=traj.algorithm_version,
    )


@router.get("/career/compare", response_model=List[CareerComparisonItemResponse])
async def compare_careers(
    career_ids: str = Query(..., description="Comma-separated career IDs to compare"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Deterministically ranks and compares multiple career options against student skill state."""
    prof = await _resolve_student_profile(db, current_user.id)
    ids = [i.strip() for i in career_ids.split(",") if i.strip()]
    if not ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide at least one career ID to compare.")

    results: List[CareerComparisonItemResponse] = []
    for c_id in ids[:5]:  # Compare up to 5
        _, calc_res = await career_intelligence_service.evaluate_career_readiness(db, prof.id, c_id)
        results.append(
            CareerComparisonItemResponse(
                career_id=calc_res.career_id,
                career_title=calc_res.career_title,
                readiness_score=float(calc_res.readiness_score),
                fit_score=float(calc_res.fit_score),
                confidence=float(calc_res.confidence),
                critical_gaps_count=len(calc_res.critical_gaps),
                status=calc_res.status,
            )
        )

    # Sort descending by readiness score
    results.sort(key=lambda x: -x.readiness_score)
    return results


# =========================================================================
# 2. Skill Intelligence Registry & Detail
# =========================================================================

@router.get("/skills", response_model=List[SkillIntelligenceResponse])
async def list_my_skills(
    tier: Optional[str] = None,
    verified_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Returns authoritative evaluated skills for the authenticated student."""
    prof = await _resolve_student_profile(db, current_user.id)
    await career_intelligence_service.evaluate_all_student_skills(db, prof.id)

    stmt = (
        select(StudentSkillIntelligenceState, SkillCatalog)
        .join(SkillCatalog, StudentSkillIntelligenceState.skill_id == SkillCatalog.id)
        .where(StudentSkillIntelligenceState.student_profile_id == prof.id)
    )

    if tier:
        stmt = stmt.where(StudentSkillIntelligenceState.proficiency_tier == tier)

    if verified_only:
        stmt = stmt.where(StudentSkillIntelligenceState.verification_status.in_(["verified", "certified"]))

    stmt = stmt.order_by(StudentSkillIntelligenceState.verified_proficiency.desc())
    records = (await db.execute(stmt)).all()

    return [
        SkillIntelligenceResponse(
            id=st.id,
            skill_id=st.skill_id,
            skill_name=skill.name,
            skill_code=skill.code,
            observed_proficiency=float(st.observed_proficiency),
            self_reported_proficiency=float(st.self_reported_proficiency) if st.self_reported_proficiency is not None else None,
            verified_proficiency=float(st.verified_proficiency),
            confidence=float(st.confidence),
            evidence_count=st.evidence_count,
            verified_evidence_count=st.verified_evidence_count,
            assessment_evidence_count=st.assessment_evidence_count,
            project_evidence_count=st.project_evidence_count,
            course_evidence_count=st.course_evidence_count,
            certification_evidence_count=st.certification_evidence_count,
            concept_mastery_contribution=float(st.concept_mastery_contribution),
            verification_status=st.verification_status,
            proficiency_tier=st.proficiency_tier,
            algorithm_version=st.algorithm_version,
            last_evaluated_at=st.last_evaluated_at,
        )
        for st, skill in records
    ]


@router.get("/skills/{skill_id}", response_model=SkillDetailResponse)
async def get_my_skill_detail(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Returns deep skill intelligence state, including full evidence records and concept associations."""
    prof = await _resolve_student_profile(db, current_user.id)
    await career_intelligence_service.evaluate_all_student_skills(db, prof.id)

    stmt = (
        select(StudentSkillIntelligenceState, SkillCatalog)
        .join(SkillCatalog, StudentSkillIntelligenceState.skill_id == SkillCatalog.id)
        .where(
            and_(
                StudentSkillIntelligenceState.student_profile_id == prof.id,
                StudentSkillIntelligenceState.skill_id == skill_id,
            )
        )
    )
    pair = (await db.execute(stmt)).first()
    if not pair:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill intelligence record not found.")

    st, skill = pair

    # Load evidence records
    ev_stmt = select(StudentSkillEvidenceRecord).where(
        and_(
            StudentSkillEvidenceRecord.student_profile_id == prof.id,
            StudentSkillEvidenceRecord.skill_id == skill_id,
        )
    ).order_by(StudentSkillEvidenceRecord.recorded_at.desc())
    ev_records = (await db.execute(ev_stmt)).scalars().all()

    return SkillDetailResponse(
        id=st.id,
        skill_id=st.skill_id,
        skill_name=skill.name,
        skill_code=skill.code,
        observed_proficiency=float(st.observed_proficiency),
        self_reported_proficiency=float(st.self_reported_proficiency) if st.self_reported_proficiency is not None else None,
        verified_proficiency=float(st.verified_proficiency),
        confidence=float(st.confidence),
        evidence_count=st.evidence_count,
        verified_evidence_count=st.verified_evidence_count,
        assessment_evidence_count=st.assessment_evidence_count,
        project_evidence_count=st.project_evidence_count,
        course_evidence_count=st.course_evidence_count,
        certification_evidence_count=st.certification_evidence_count,
        concept_mastery_contribution=float(st.concept_mastery_contribution),
        verification_status=st.verification_status,
        proficiency_tier=st.proficiency_tier,
        algorithm_version=st.algorithm_version,
        last_evaluated_at=st.last_evaluated_at,
        evidence_records=[
            SkillEvidenceRecordResponse(
                id=ev.id,
                source_type=ev.source_type,
                source_id=ev.source_id,
                evidence_score=float(ev.evidence_score),
                evidence_weight=float(ev.evidence_weight),
                is_verified=ev.is_verified,
                provenance_details=ev.provenance_details,
                recorded_at=ev.recorded_at,
            )
            for ev in ev_records
        ],
        associated_concepts=[],
    )


# =========================================================================
# 3. Scoped Faculty, Placement Officer & Institutional Views
# =========================================================================

@router.get("/students/{student_id}/career/intelligence", response_model=CareerIntelligenceOverviewResponse)
async def get_student_career_intelligence_by_id(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.TEACHER,
            UserRole.HOD,
            UserRole.PLACEMENT_OFFICER,
            UserRole.INSTITUTION_ADMIN,
            UserRole.SUPER_ADMIN,
        )
    ),
):
    """Faculty/Placement Officer/Admin endpoint to view student career intelligence within authorized scope."""
    stmt = select(StudentAcademicProfile).where(
        or_(
            StudentAcademicProfile.id == student_id,
            StudentAcademicProfile.user_id == student_id,
        )
    )
    prof = (await db.execute(stmt)).scalar_one_or_none()
    if not prof:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student academic profile not found.")

    # Institutional isolation
    if current_user.role != UserRole.SUPER_ADMIN:
        if prof.institution_id != current_user.institution_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied across institutional boundary.")

    # Evaluate readiness
    c_state, calc_res = await career_intelligence_service.evaluate_career_readiness(db, prof.id)

    readiness_dto = CareerReadinessResponse(
        career_id=calc_res.career_id,
        career_title=calc_res.career_title,
        readiness_score=float(calc_res.readiness_score),
        fit_score=float(calc_res.fit_score),
        confidence=float(calc_res.confidence),
        required_skill_coverage=float(calc_res.required_skill_coverage),
        preferred_skill_coverage=float(calc_res.preferred_skill_coverage),
        critical_skill_coverage=float(calc_res.critical_skill_coverage),
        critical_gaps_count=len(calc_res.critical_gaps),
        strengths_count=len(calc_res.strengths),
        developing_count=len(calc_res.developing),
        status=calc_res.status,
        explanation=calc_res.explanation,
        critical_gaps=[],
        strengths=[],
        developing=[],
        algorithm_version=calc_res.algorithm_version,
    )

    traj = await career_intelligence_service.generate_career_trajectory(db, prof.id, c_state.career_id)
    traj_dto = CareerTrajectoryResponse(
        career_id=traj.career_id,
        career_title=calc_res.career_title,
        status=traj.status,
        total_steps=traj.total_steps,
        completed_steps=traj.completed_steps,
        steps=[],
        algorithm_version=traj.algorithm_version,
    )

    p_state = await career_intelligence_service.evaluate_placement_readiness(db, prof.id)
    placement_dto = PlacementReadinessResponse(
        technical_readiness=float(p_state.technical_readiness) if p_state.technical_readiness is not None else None,
        assessment_readiness=float(p_state.assessment_readiness) if p_state.assessment_readiness is not None else None,
        project_evidence_score=float(p_state.project_evidence_score) if p_state.project_evidence_score is not None else None,
        communication_readiness=float(p_state.communication_readiness) if p_state.communication_readiness is not None else None,
        resume_readiness=float(p_state.resume_readiness) if p_state.resume_readiness is not None else None,
        interview_readiness=float(p_state.interview_readiness) if p_state.interview_readiness is not None else None,
        career_alignment=float(p_state.career_alignment) if p_state.career_alignment is not None else None,
        overall_status=p_state.overall_status,
        component_statuses=p_state.component_statuses,
        algorithm_version=p_state.algorithm_version,
    )

    return CareerIntelligenceOverviewResponse(
        target_career=readiness_dto,
        readiness=readiness_dto,
        trajectory=traj_dto,
        placement=placement_dto,
        total_skills_tracked=0,
        verified_skills_count=0,
        algorithm_version=calc_res.algorithm_version,
    )
