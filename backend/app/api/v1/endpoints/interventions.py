"""REST API endpoints for Student Interventions and Follow-Up Actions."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, require_roles
from app.core.security import UserRole
from app.domains.identity.models import User
from app.domains.profiles.service import profile_service
from app.domains.profiles.schemas import (
    StudentInterventionCreate,
    StudentInterventionUpdate,
    StudentInterventionResolveRequest,
    StudentInterventionResponse,
)

router = APIRouter(prefix="/interventions", tags=["Interventions & Support Tracking"])


@router.get("", response_model=List[StudentInterventionResponse])
async def list_interventions(
    student_profile_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.MENTOR, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """List student interventions scoped to the institution."""
    inst_id = current_user.institution_id if current_user.role != UserRole.SUPER_ADMIN else None
    return await profile_service.list_interventions(
        db, student_profile_id=student_profile_id, institution_id=inst_id, status_filter=status_filter
    )


@router.post("", response_model=StudentInterventionResponse, status_code=status.HTTP_201_CREATED)
async def create_intervention(
    data: StudentInterventionCreate,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.MENTOR, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Create a structured academic, attendance, course, or career support intervention."""
    return await profile_service.create_intervention(db, data, current_user)


@router.post("/{intervention_id}/resolve", response_model=StudentInterventionResponse)
async def resolve_intervention(
    intervention_id: str,
    data: StudentInterventionResolveRequest,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.MENTOR, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Mark an intervention resolved with auditable outcome notes."""
    return await profile_service.resolve_intervention(db, intervention_id, data.resolution_notes, current_user)
