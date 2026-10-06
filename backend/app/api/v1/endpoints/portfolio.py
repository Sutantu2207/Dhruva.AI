"""REST Endpoints for Domain 8: Portfolio Intelligence & Portfolio Builder."""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, get_current_user, require_roles
from app.core.security import UserRole
from app.domains.identity.models import User
from app.domains.academic.models import StudentAcademicProfile
from app.domains.project_intelligence.service import project_intelligence_service
from app.domains.project_intelligence.schemas import (
    PortfolioUpdate,
    PortfolioResponse,
    PortfolioHealthResultSchema,
)

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


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


@router.get("", response_model=PortfolioResponse)
async def get_my_portfolio(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Retrieves current student's portfolio configuration."""
    prof = await _resolve_student_profile(db, current_user.id)
    port = await project_intelligence_service.get_or_create_portfolio(db, prof.id)
    await db.commit()
    return PortfolioResponse(
        id=port.id,
        student_profile_id=port.student_profile_id,
        slug=port.slug,
        theme=port.theme,
        headline=port.headline,
        bio=port.bio,
        contact_email=port.contact_email,
        social_links=port.social_links or {},
        custom_links=port.custom_links or [],
        featured_project_ids=port.featured_project_ids or [],
        featured_skill_ids=port.featured_skill_ids or [],
        featured_certification_ids=port.featured_certification_ids or [],
        featured_achievement_ids=port.featured_achievement_ids or [],
        public_visibility=port.public_visibility,
        custom_domain=getattr(port, "custom_domain", None),
        created_at=port.created_at,
        updated_at=port.updated_at,
    )


@router.patch("", response_model=PortfolioResponse)
async def update_my_portfolio(
    data: PortfolioUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Updates student portfolio configuration and preferences."""
    prof = await _resolve_student_profile(db, current_user.id)
    try:
        port = await project_intelligence_service.update_portfolio(
            db=db,
            student_profile_id=prof.id,
            data=data.model_dump(exclude_unset=True),
        )
        await db.commit()
        return PortfolioResponse(
            id=port.id,
            student_profile_id=port.student_profile_id,
            slug=port.slug,
            theme=port.theme,
            headline=port.headline,
            bio=port.bio,
            contact_email=port.contact_email,
            social_links=port.social_links or {},
            custom_links=port.custom_links or [],
            featured_project_ids=port.featured_project_ids or [],
            featured_skill_ids=port.featured_skill_ids or [],
            featured_certification_ids=port.featured_certification_ids or [],
            featured_achievement_ids=port.featured_achievement_ids or [],
            public_visibility=port.public_visibility,
            custom_domain=getattr(port, "custom_domain", None),
            created_at=port.created_at,
            updated_at=port.updated_at,
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/health", response_model=PortfolioHealthResultSchema)
async def get_my_portfolio_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Deterministic evaluation of student portfolio health, completeness, and missing sections."""
    prof = await _resolve_student_profile(db, current_user.id)
    h_res = await project_intelligence_service.evaluate_portfolio_health(db, prof.id)
    await db.commit()
    return PortfolioHealthResultSchema(
        overall_health_score=h_res.overall_health_score,
        status=h_res.status,
        technical_depth=h_res.technical_depth,
        project_diversity=h_res.project_diversity,
        evidence_quality=h_res.evidence_quality,
        documentation_quality=h_res.documentation_quality,
        career_alignment=h_res.career_alignment,
        professional_presence=h_res.professional_presence,
        verification_coverage=h_res.verification_coverage,
        completeness_score=h_res.completeness_score,
        missing_sections=h_res.missing_sections,
        dimension_explanations=h_res.dimension_explanations,
        recommendations=[f"Complete missing section: {s}" for s in h_res.missing_sections],
        algorithm_version=h_res.algorithm_version,
    )


@router.get("/public/{slug_or_username}")
async def get_public_portfolio_view(
    slug_or_username: str,
    db: AsyncSession = Depends(get_db),
):
    """Safe public portfolio view. Never exposes private internal notes, reviews, or unverified items."""
    data = await project_intelligence_service.get_public_portfolio(db, slug_or_username)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Public portfolio not found or visibility is set to private.",
        )
    return data
