"""REST Endpoints for Domain 8: Skill Graph & Multi-Dimensional Evidence Traversals."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, get_current_user, require_roles
from app.core.security import UserRole
from app.domains.identity.models import User
from app.domains.academic.models import StudentAcademicProfile
from app.domains.project_intelligence.graph_service import skill_graph_service
from app.domains.project_intelligence.schemas import (
    SkillEvidenceGraphResponse,
    StudentSkillGraphResponse,
)

router = APIRouter(tags=["skill-graph"])


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


@router.get("/skills/{skill_id}/graph", response_model=SkillEvidenceGraphResponse)
async def get_skill_evidence_graph(
    skill_id: str,
    student_profile_id: Optional[str] = Query(None, description="Optional profile ID for faculty/admin inspection"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Answers: 'Why does Dhruva think this student has this skill?' with complete deterministic provenance."""
    target_prof_id = student_profile_id
    if not target_prof_id:
        if current_user.role == UserRole.STUDENT:
            prof = await _resolve_student_profile(db, current_user.id)
            target_prof_id = prof.id
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="student_profile_id required for non-student inspection.",
            )

    graph_data = await skill_graph_service.get_skill_evidence_graph(
        db=db,
        skill_id=skill_id,
        student_profile_id=target_prof_id,
    )

    if "error" in graph_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=graph_data["error"])

    return graph_data


@router.get("/students/me/skill-graph", response_model=StudentSkillGraphResponse)
async def get_my_skill_graph(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Traverses and returns the student's full multi-dimensional skill graph."""
    prof = await _resolve_student_profile(db, current_user.id)
    return await skill_graph_service.get_student_skill_graph(db, prof.id)


@router.get("/students/me/projects/gap-strengthening")
async def get_projects_strengthening_gaps(
    career_id: Optional[str] = Query(None, description="Career catalog ID to check gaps for"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Finds projects demonstrating skills that bridge student's primary career gaps."""
    prof = await _resolve_student_profile(db, current_user.id)
    return await skill_graph_service.find_projects_strengthening_gap(
        db=db,
        student_profile_id=prof.id,
        career_id=career_id,
    )


@router.get("/students/me/projects/insufficient-evidence")
async def get_projects_with_insufficient_evidence(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Identifies student projects that lack verified empirical evidence or documentation."""
    prof = await _resolve_student_profile(db, current_user.id)
    return await skill_graph_service.find_projects_with_insufficient_evidence(
        db=db,
        student_profile_id=prof.id,
    )
