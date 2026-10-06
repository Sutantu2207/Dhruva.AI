"""REST API endpoints for Bulk Student and Faculty Onboarding Imports."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, require_roles
from app.core.security import UserRole
from app.domains.identity.models import User
from app.domains.profiles.models import OnboardingImportJob
from app.domains.profiles.onboarding import OnboardingEngine
from app.domains.profiles.service import profile_service
from app.domains.profiles.schemas import (
    OnboardingImportRequest,
    OnboardingImportJobResponse,
    AdminInstitutionOverview,
)

router = APIRouter(prefix="/imports", tags=["Onboarding & Bulk Ingestion"])


@router.post("/students", response_model=OnboardingImportJobResponse, status_code=status.HTTP_201_CREATED)
async def bulk_import_students(
    data: OnboardingImportRequest,
    current_user: User = Depends(require_roles(UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Safely validate and ingest bulk student records with duplicate detection & formula injection defense."""
    job = await OnboardingEngine.import_students(
        db=db,
        admin_user=current_user,
        records=data.records,
        file_name=data.file_name,
        is_dry_run=data.is_dry_run,
    )
    return job


@router.post("/faculty", response_model=OnboardingImportJobResponse, status_code=status.HTTP_201_CREATED)
async def bulk_import_faculty(
    data: OnboardingImportRequest,
    current_user: User = Depends(require_roles(UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Safely validate and ingest bulk faculty records with duplicate detection."""
    job = await OnboardingEngine.import_faculty(
        db=db,
        admin_user=current_user,
        records=data.records,
        file_name=data.file_name,
        is_dry_run=data.is_dry_run,
    )
    return job


@router.get("/{job_id}", response_model=OnboardingImportJobResponse)
async def get_import_job(
    job_id: str,
    current_user: User = Depends(require_roles(UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """View status, error breakdown, and metrics of an onboarding import job."""
    stmt = select(OnboardingImportJob).where(OnboardingImportJob.id == job_id)
    job = (await db.execute(stmt)).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found.")

    if current_user.role != UserRole.SUPER_ADMIN and job.institution_id != current_user.institution_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return job


@router.get("/admin/overview", response_model=AdminInstitutionOverview)
async def get_admin_overview(
    current_user: User = Depends(require_roles(UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Database-calculated metrics and status distributions for institution administrators."""
    inst_id = current_user.institution_id
    if not inst_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Administrator has no assigned institution.")
    return await profile_service.get_admin_institution_overview(db, inst_id)
