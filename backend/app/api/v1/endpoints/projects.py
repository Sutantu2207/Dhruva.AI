"""REST Endpoints for Domain 8: Project Intelligence & Project Evidence Engine."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_user, require_roles
from app.core.security import UserRole
from app.domains.identity.models import User
from app.domains.academic.models import StudentAcademicProfile
from app.domains.profiles.models import StudentProject, StudentProjectSkill
from app.domains.project_intelligence.models import ProjectEvidence, ProjectReview
from app.domains.project_intelligence.service import project_intelligence_service
from app.domains.project_intelligence.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectDetailResponse,
    ProjectSkillResponse,
    ProjectConceptResponse,
    ProjectEvidenceCreate,
    ProjectEvidenceVerify,
    ProjectEvidenceResponse,
    ProjectReviewCreate,
    ProjectReviewResponse,
    ProjectQualityResultSchema,
    CareerRelevanceResultSchema,
)

router = APIRouter(prefix="/projects", tags=["projects"])


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


def _map_project_to_response(project: StudentProject) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        student_profile_id=project.student_profile_id,
        title=project.title,
        slug=project.slug,
        short_description=project.short_description,
        description=project.description,
        problem_statement=project.problem_statement,
        solution=project.solution,
        project_type=project.project_type,
        status=project.status,
        start_date=project.start_date,
        end_date=project.end_date,
        technologies=project.technologies or [],
        repository_url=project.repository_url,
        live_url=project.live_url,
        demo_url=project.demo_url,
        documentation_url=project.documentation_url,
        visibility=project.visibility,
        team_or_individual=project.team_or_individual,
        role=project.role,
        team_size=project.team_size,
        contribution_description=project.contribution_description,
        contribution_percentage=float(project.contribution_percentage) if project.contribution_percentage is not None else None,
        modules_contributed=project.modules_contributed or [],
        verification_status=project.verification_status,
        is_verified=project.is_verified,
        verified_by_user_id=project.verified_by_user_id,
        quality_score=project.quality_score,
        career_relevance_score=project.career_relevance_score,
        career_relevance_category=project.career_relevance_category,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def _map_project_to_detail(project: StudentProject) -> ProjectDetailResponse:
    base = _map_project_to_response(project)
    
    skills = [
        ProjectSkillResponse(
            id=ps.id,
            project_id=ps.project_id,
            skill_catalog_id=ps.skill_catalog_id,
            skill_name=ps.skill_catalog.name if ps.skill_catalog else ps.skill_catalog_id,
            skill_category=ps.skill_catalog.category if ps.skill_catalog else None,
            claimed_level=ps.claimed_level,
            observed_level=ps.observed_level,
            evidence_strength=ps.evidence_strength,
            verification_status=ps.verification_status,
            verified_by_user_id=ps.verified_by_user_id,
            verified_at=ps.verified_at,
            source=ps.source,
            notes=ps.notes,
        )
        for ps in (project.project_skills or [])
    ]

    concepts = [
        ProjectConceptResponse(
            id=pc.id,
            project_id=pc.project_id,
            concept_id=pc.concept_id,
            concept_name=pc.concept.name if pc.concept else pc.concept_id,
            demonstrated_level=pc.demonstrated_level,
            verification_status=pc.verification_status,
            verified_by_user_id=pc.verified_by_user_id,
            verified_at=pc.verified_at,
            notes=pc.notes,
        )
        for pc in (project.project_concepts or [])
    ]

    evidence = [
        ProjectEvidenceResponse(
            id=ev.id,
            project_id=ev.project_id,
            student_profile_id=ev.student_profile_id,
            evidence_type=ev.evidence_type,
            source=ev.source,
            source_reference=ev.source_reference,
            title=ev.title,
            description=ev.description,
            submitted_at=ev.submitted_at,
            verification_status=ev.verification_status,
            verified_by_user_id=ev.verified_by_user_id,
            verified_at=ev.verified_at,
            evidence_strength=ev.evidence_strength,
            metadata_json=ev.metadata_json,
        )
        for ev in (project.evidence_items or [])
    ]

    reviews = [
        ProjectReviewResponse(
            id=r.id,
            project_id=r.id,
            reviewer_user_id=r.reviewer_user_id,
            reviewer_name=f"{r.reviewer.first_name} {r.reviewer.last_name}" if r.reviewer else "Faculty Reviewer",
            review_type=r.review_type,
            technical_depth=r.technical_depth,
            problem_solving=r.problem_solving,
            code_quality=r.code_quality,
            architecture_quality=r.architecture_quality,
            documentation_quality=r.documentation_quality,
            testing_quality=r.testing_quality,
            practical_application=r.practical_application,
            originality=r.originality,
            student_contribution_score=r.student_contribution_score,
            professional_presentation=r.professional_presentation,
            overall_score=r.overall_score,
            rubric_breakdown=r.rubric_breakdown or {},
            feedback=r.feedback,
            decision=r.decision,
            is_finalized=r.is_finalized,
            reviewed_at=r.reviewed_at,
        )
        for r in (project.reviews or [])
    ]

    return ProjectDetailResponse(
        **base.model_dump(),
        skills=skills,
        concepts=concepts,
        evidence=evidence,
        reviews=reviews,
        quality_breakdown=project.quality_breakdown,
    )


# =========================================================================
# 1. Project CRUD Endpoints
# =========================================================================

@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    student_profile_id: Optional[str] = Query(None, description="Optional profile ID for faculty/admin inspection"),
    project_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    is_verified: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists student projects with optional category and status filtering."""
    target_prof_id = student_profile_id
    if not target_prof_id:
        if current_user.role == UserRole.STUDENT:
            prof = await _resolve_student_profile(db, current_user.id)
            target_prof_id = prof.id
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="student_profile_id required for non-student viewers.",
            )

    stmt = select(StudentProject).where(StudentProject.student_profile_id == target_prof_id)
    if project_type:
        stmt = stmt.where(StudentProject.project_type == project_type)
    if status_filter:
        stmt = stmt.where(StudentProject.status == status_filter)
    if is_verified is not None:
        stmt = stmt.where(StudentProject.is_verified == is_verified)

    # Visibility filter if accessed by external user
    if current_user.role == UserRole.STUDENT:
        prof = await _resolve_student_profile(db, current_user.id)
        if prof.id != target_prof_id:
            stmt = stmt.where(StudentProject.visibility.in_(["public", "institution"]))
    
    stmt = stmt.order_by(StudentProject.created_at.desc())
    projects = (await db.execute(stmt)).scalars().all()
    return [_map_project_to_response(p) for p in projects]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Creates a new canonical project for the authenticated student."""
    prof = await _resolve_student_profile(db, current_user.id)
    try:
        project = await project_intelligence_service.create_project(
            db=db,
            student_profile_id=prof.id,
            data=data.model_dump(),
        )
        await db.commit()
        return _map_project_to_response(project)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves rich project intelligence details."""
    project = await project_intelligence_service.get_project_with_details(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    # Authorization / Visibility check
    if current_user.role == UserRole.STUDENT:
        prof = await _resolve_student_profile(db, current_user.id)
        if project.student_profile_id != prof.id and project.visibility == "private":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to private project.")

    return _map_project_to_detail(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Updates student project metadata and triggers deterministic quality recalculation."""
    prof = await _resolve_student_profile(db, current_user.id)
    try:
        project = await project_intelligence_service.update_project(
            db=db,
            project_id=project_id,
            student_profile_id=prof.id,
            data=data.model_dump(exclude_unset=True),
        )
        await db.commit()
        return _map_project_to_response(project)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Deletes or archives a project owned by the authenticated student."""
    prof = await _resolve_student_profile(db, current_user.id)
    try:
        await project_intelligence_service.delete_project(
            db=db,
            project_id=project_id,
            student_profile_id=prof.id,
        )
        await db.commit()
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =========================================================================
# 2. Project Evidence Endpoints
# =========================================================================

@router.get("/{project_id}/evidence", response_model=List[ProjectEvidenceResponse])
async def list_project_evidence(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists all empirical evidence records associated with the project."""
    project = await db.get(StudentProject, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    if current_user.role == UserRole.STUDENT:
        prof = await _resolve_student_profile(db, current_user.id)
        if project.student_profile_id != prof.id and project.visibility == "private":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    stmt = select(ProjectEvidence).where(ProjectEvidence.project_id == project_id).order_by(ProjectEvidence.submitted_at.desc())
    items = (await db.execute(stmt)).scalars().all()
    return [
        ProjectEvidenceResponse(
            id=ev.id,
            project_id=ev.project_id,
            student_profile_id=ev.student_profile_id,
            evidence_type=ev.evidence_type,
            source=ev.source,
            source_reference=ev.source_reference,
            title=ev.title,
            description=ev.description,
            submitted_at=ev.submitted_at,
            verification_status=ev.verification_status,
            verified_by_user_id=ev.verified_by_user_id,
            verified_at=ev.verified_at,
            evidence_strength=ev.evidence_strength,
            metadata_json=ev.metadata_json,
        )
        for ev in items
    ]


@router.post("/{project_id}/evidence", response_model=ProjectEvidenceResponse, status_code=status.HTTP_201_CREATED)
async def submit_project_evidence(
    project_id: str,
    data: ProjectEvidenceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Student submits a verifiable empirical evidence item for their project."""
    prof = await _resolve_student_profile(db, current_user.id)
    try:
        ev = await project_intelligence_service.add_project_evidence(
            db=db,
            project_id=project_id,
            student_profile_id=prof.id,
            evidence_in=data.model_dump(),
        )
        await db.commit()
        return ProjectEvidenceResponse(
            id=ev.id,
            project_id=ev.project_id,
            student_profile_id=ev.student_profile_id,
            evidence_type=ev.evidence_type,
            source=ev.source,
            source_reference=ev.source_reference,
            title=ev.title,
            description=ev.description,
            submitted_at=ev.submitted_at,
            verification_status=ev.verification_status,
            verified_by_user_id=ev.verified_by_user_id,
            verified_at=ev.verified_at,
            evidence_strength=ev.evidence_strength,
            metadata_json=ev.metadata_json,
        )
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{project_id}/evidence/{evidence_id}/verify", response_model=ProjectEvidenceResponse)
async def verify_project_evidence(
    project_id: str,
    evidence_id: str,
    decision_in: ProjectEvidenceVerify,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(
        UserRole.TEACHER, UserRole.MENTOR, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN
    )),
):
    """Authorized reviewer verifies or rejects an evidence record (students barred from self-verification)."""
    try:
        ev = await project_intelligence_service.verify_project_evidence(
            db=db,
            evidence_id=evidence_id,
            reviewer_user=current_user,
            decision=decision_in.decision,
            verification_notes=decision_in.verification_notes,
        )
        await db.commit()
        return ProjectEvidenceResponse(
            id=ev.id,
            project_id=ev.project_id,
            student_profile_id=ev.student_profile_id,
            evidence_type=ev.evidence_type,
            source=ev.source,
            source_reference=ev.source_reference,
            title=ev.title,
            description=ev.description,
            submitted_at=ev.submitted_at,
            verification_status=ev.verification_status,
            verified_by_user_id=ev.verified_by_user_id,
            verified_at=ev.verified_at,
            evidence_strength=ev.evidence_strength,
            metadata_json=ev.metadata_json,
        )
    except PermissionError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =========================================================================
# 3. Faculty Project Review Workflow
# =========================================================================

@router.get("/{project_id}/reviews", response_model=List[ProjectReviewResponse])
async def list_project_reviews(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves all rubric reviews submitted for this project."""
    stmt = (
        select(ProjectReview)
        .options(selectinload(ProjectReview.reviewer))
        .where(ProjectReview.project_id == project_id)
        .order_by(ProjectReview.reviewed_at.desc())
    )
    reviews = (await db.execute(stmt)).scalars().all()
    return [
        ProjectReviewResponse(
            id=r.id,
            project_id=r.project_id,
            reviewer_user_id=r.reviewer_user_id,
            reviewer_name=f"{r.reviewer.first_name} {r.reviewer.last_name}" if r.reviewer else "Faculty Reviewer",
            review_type=r.review_type,
            technical_depth=r.technical_depth,
            problem_solving=r.problem_solving,
            code_quality=r.code_quality,
            architecture_quality=r.architecture_quality,
            documentation_quality=r.documentation_quality,
            testing_quality=r.testing_quality,
            practical_application=r.practical_application,
            originality=r.originality,
            student_contribution_score=r.student_contribution_score,
            professional_presentation=r.professional_presentation,
            overall_score=r.overall_score,
            rubric_breakdown=r.rubric_breakdown or {},
            feedback=r.feedback,
            decision=r.decision,
            is_finalized=r.is_finalized,
            reviewed_at=r.reviewed_at,
        )
        for r in reviews
    ]


@router.post("/{project_id}/reviews", response_model=ProjectReviewResponse, status_code=status.HTTP_201_CREATED)
async def submit_project_review(
    project_id: str,
    data: ProjectReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(
        UserRole.TEACHER, UserRole.MENTOR, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN
    )),
):
    """Faculty/mentor submits an immutable 10-dimension rubric review."""
    try:
        rev = await project_intelligence_service.submit_faculty_review(
            db=db,
            project_id=project_id,
            reviewer_user=current_user,
            review_data=data.model_dump(),
        )
        await db.commit()
        return ProjectReviewResponse(
            id=rev.id,
            project_id=rev.project_id,
            reviewer_user_id=rev.reviewer_user_id,
            reviewer_name=f"{current_user.first_name} {current_user.last_name}",
            review_type=rev.review_type,
            technical_depth=rev.technical_depth,
            problem_solving=rev.problem_solving,
            code_quality=rev.code_quality,
            architecture_quality=rev.architecture_quality,
            documentation_quality=rev.documentation_quality,
            testing_quality=rev.testing_quality,
            practical_application=rev.practical_application,
            originality=rev.originality,
            student_contribution_score=rev.student_contribution_score,
            professional_presentation=rev.professional_presentation,
            overall_score=rev.overall_score,
            rubric_breakdown=rev.rubric_breakdown or {},
            feedback=rev.feedback,
            decision=rev.decision,
            is_finalized=rev.is_finalized,
            reviewed_at=rev.reviewed_at,
        )
    except PermissionError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =========================================================================
# 4. Deterministic Intelligence Scoring
# =========================================================================

@router.get("/{project_id}/quality", response_model=ProjectQualityResultSchema)
async def get_project_quality(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deterministic explainable quality score breakdown across 6 technical dimensions."""
    try:
        q_res, _ = await project_intelligence_service.recalculate_project_intelligence(db, project_id)
        await db.commit()
        return ProjectQualityResultSchema(
            overall_score=q_res.overall_score,
            technical_depth=q_res.technical_depth,
            implementation_quality=q_res.implementation_quality,
            documentation_quality=q_res.documentation_quality,
            testing_quality=q_res.testing_quality,
            architecture_quality=q_res.architecture_quality,
            verification_strength=q_res.verification_strength,
            dimension_breakdown=q_res.dimension_breakdown,
            missing_elements=q_res.missing_elements,
            algorithm_version=q_res.algorithm_version,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{project_id}/career-relevance", response_model=Optional[CareerRelevanceResultSchema])
async def get_project_career_relevance(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Calculates deterministic career relevance of the project against target career goal."""
    try:
        _, rel_res = await project_intelligence_service.recalculate_project_intelligence(db, project_id)
        await db.commit()
        if not rel_res:
            return None
        return CareerRelevanceResultSchema(
            project_id=rel_res.project_id,
            career_id=rel_res.career_id,
            career_title=rel_res.career_title,
            relevance_score=rel_res.relevance_score,
            relevance_tier=rel_res.relevance_tier,
            matched_skills_count=rel_res.matched_skills_count,
            critical_skills_matched=rel_res.critical_skills_matched,
            missing_critical_skills=rel_res.missing_critical_skills,
            explanation=rel_res.explanation,
            algorithm_version=rel_res.algorithm_version,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
