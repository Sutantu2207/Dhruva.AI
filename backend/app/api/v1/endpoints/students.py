"""REST API endpoints for Student Profiles, Skills, Career Goals, Projects, Portfolio & Resume."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, require_roles
from app.core.security import UserRole
from app.domains.identity.models import User
from app.domains.academic.models import StudentAcademicProfile
from app.domains.profiles.service import profile_service
from app.domains.profiles.schemas import (
    StudentProfileDetailUpdate,
    StudentProfileDetailResponse,
    StudentAcademicStatusChangeRequest,
    StudentAcademicStatusHistoryResponse,
    StudentSkillCreate,
    StudentSkillUpdate,
    StudentSkillResponse,
    StudentInterestCreate,
    StudentInterestResponse,
    StudentCareerGoalCreate,
    StudentCareerGoalUpdate,
    StudentCareerGoalResponse,
    StudentProjectCreate,
    StudentProjectUpdate,
    StudentProjectResponse,
    StudentCertificationCreate,
    StudentCertificationUpdate,
    StudentCertificationVerifyRequest,
    StudentCertificationResponse,
    StudentAchievementCreate,
    StudentAchievementUpdate,
    StudentAchievementResponse,
    StudentPortfolioUpdate,
    StudentPortfolioResponse,
    StudentResumeUpdate,
    StudentResumeResponse,
    StudentDashboardOverview,
)

router = APIRouter(prefix="/students", tags=["Students & Academic Profiles"])


# =========================================================================
# 1. Student Identity & Extended Profile
# =========================================================================

@router.get("/me", response_model=StudentProfileDetailResponse)
async def get_my_student_profile(
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the authenticated student's extended biographical and contact profile."""
    acad_profile = await profile_service.get_student_academic_profile_by_user(db, current_user.id)
    detail = await profile_service.get_or_create_student_detail(db, acad_profile.id)
    return detail


@router.patch("/me", response_model=StudentProfileDetailResponse)
async def update_my_student_profile(
    data: StudentProfileDetailUpdate,
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Update authenticated student's permitted biographical and contact details."""
    acad_profile = await profile_service.get_student_academic_profile_by_user(db, current_user.id)
    detail = await profile_service.update_student_detail(db, acad_profile.id, data, current_user)
    return detail


@router.get("/me/overview", response_model=StudentDashboardOverview)
async def get_my_dashboard_overview(
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Deterministic, database-backed overview for the authenticated student's workspace."""
    return await profile_service.get_student_dashboard_overview(db, current_user.id)


@router.get("/{student_profile_id}/overview", response_model=StudentDashboardOverview)
async def get_student_overview_scoped(
    student_profile_id: str,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.MENTOR, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Authorized overview for elevated faculty, mentors, and administrators."""
    acad_profile = await profile_service.get_student_academic_profile(db, student_profile_id)
    # Institutional isolation
    if current_user.role != UserRole.SUPER_ADMIN and current_user.institution_id != acad_profile.institution_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access students outside your institution.")
    return await profile_service.get_student_dashboard_overview(db, acad_profile.user_id)


# =========================================================================
# 2. Academic Status History
# =========================================================================

@router.get("/{student_profile_id}/status-history", response_model=List[StudentAcademicStatusHistoryResponse])
async def get_student_status_history(
    student_profile_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """View auditable academic status history."""
    acad_profile = await profile_service.get_student_academic_profile(db, student_profile_id)
    if current_user.role == UserRole.STUDENT and acad_profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    if current_user.role != UserRole.SUPER_ADMIN and current_user.institution_id != acad_profile.institution_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return await profile_service.get_student_status_history(db, student_profile_id)


@router.post("/{student_profile_id}/status", status_code=status.HTTP_200_OK)
async def change_student_status(
    student_profile_id: str,
    data: StudentAcademicStatusChangeRequest,
    current_user: User = Depends(require_roles(UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Transition student academic status with immutable audit logging."""
    return await profile_service.change_student_academic_status(db, student_profile_id, data, current_user)


# =========================================================================
# 3. Student Skills
# =========================================================================

@router.get("/me/skills", response_model=List[StudentSkillResponse])
async def list_my_skills(
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all skills mapped to the student profile."""
    acad_profile = await profile_service.get_student_academic_profile_by_user(db, current_user.id)
    skills = await profile_service.list_student_skills(db, acad_profile.id)
    return [
        StudentSkillResponse(
            id=s.id,
            student_profile_id=s.student_profile_id,
            skill_catalog_id=s.skill_catalog_id,
            skill_name=s.skill_catalog.name if s.skill_catalog else "",
            skill_code=s.skill_catalog.code if s.skill_catalog else "",
            proficiency=s.proficiency,
            source=s.source,
            is_verified=s.is_verified,
            verified_by_user_id=s.verified_by_user_id,
            last_assessed_at=s.last_assessed_at,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in skills
    ]


@router.post("/me/skills", response_model=StudentSkillResponse, status_code=status.HTTP_201_CREATED)
async def add_my_skill(
    data: StudentSkillCreate,
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Map a canonical skill from SkillCatalog to the student profile."""
    acad_profile = await profile_service.get_student_academic_profile_by_user(db, current_user.id)
    s = await profile_service.add_student_skill(db, acad_profile.id, data, current_user)
    return StudentSkillResponse(
        id=s.id,
        student_profile_id=s.student_profile_id,
        skill_catalog_id=s.skill_catalog_id,
        skill_name="",
        skill_code="",
        proficiency=s.proficiency,
        source=s.source,
        is_verified=s.is_verified,
        verified_by_user_id=s.verified_by_user_id,
        last_assessed_at=s.last_assessed_at,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


@router.patch("/me/skills/{skill_id}", response_model=StudentSkillResponse)
async def update_my_skill(
    skill_id: str,
    data: StudentSkillUpdate,
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Update proficiency or self-declared details for a mapped skill."""
    s = await profile_service.update_student_skill(db, skill_id, data, current_user)
    return StudentSkillResponse(
        id=s.id,
        student_profile_id=s.student_profile_id,
        skill_catalog_id=s.skill_catalog_id,
        skill_name="",
        skill_code="",
        proficiency=s.proficiency,
        source=s.source,
        is_verified=s.is_verified,
        verified_by_user_id=s.verified_by_user_id,
        last_assessed_at=s.last_assessed_at,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


@router.delete("/me/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_skill(
    skill_id: str,
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Remove a skill from the student profile."""
    acad_profile = await profile_service.get_student_academic_profile_by_user(db, current_user.id)
    await profile_service.delete_student_skill(db, skill_id, acad_profile.id)


# =========================================================================
# 4. Student Career Goals & Interests
# =========================================================================

@router.get("/me/career-goals", response_model=List[StudentCareerGoalResponse])
async def list_my_career_goals(
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    acad_profile = await profile_service.get_student_academic_profile_by_user(db, current_user.id)
    goals = await profile_service.list_student_career_goals(db, acad_profile.id)
    return [
        StudentCareerGoalResponse(
            id=g.id,
            student_profile_id=g.student_profile_id,
            career_catalog_id=g.career_catalog_id,
            career_title=g.career_catalog.title if g.career_catalog else "",
            career_code=g.career_catalog.code if g.career_catalog else "",
            priority=g.priority,
            short_term_goals=g.short_term_goals,
            long_term_goals=g.long_term_goals,
            target_industry=g.target_industry,
            preferred_locations=g.preferred_locations,
            target_organizations=g.target_organizations,
            created_at=g.created_at,
            updated_at=g.updated_at,
        )
        for g in goals
    ]


@router.post("/me/career-goals", response_model=StudentCareerGoalResponse, status_code=status.HTTP_201_CREATED)
async def add_my_career_goal(
    data: StudentCareerGoalCreate,
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    acad_profile = await profile_service.get_student_academic_profile_by_user(db, current_user.id)
    g = await profile_service.add_student_career_goal(db, acad_profile.id, data)
    return StudentCareerGoalResponse(
        id=g.id,
        student_profile_id=g.student_profile_id,
        career_catalog_id=g.career_catalog_id,
        career_title="",
        career_code="",
        priority=g.priority,
        short_term_goals=g.short_term_goals,
        long_term_goals=g.long_term_goals,
        target_industry=g.target_industry,
        preferred_locations=g.preferred_locations,
        target_organizations=g.target_organizations,
        created_at=g.created_at,
        updated_at=g.updated_at,
    )


@router.delete("/me/career-goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_career_goal(
    goal_id: str,
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    acad_profile = await profile_service.get_student_academic_profile_by_user(db, current_user.id)
    await profile_service.delete_student_career_goal(db, goal_id, acad_profile.id)


@router.get("/me/interests", response_model=List[StudentInterestResponse])
async def list_my_interests(
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    acad_profile = await profile_service.get_student_academic_profile_by_user(db, current_user.id)
    return await profile_service.list_student_interests(db, acad_profile.id)


@router.post("/me/interests", response_model=StudentInterestResponse, status_code=status.HTTP_201_CREATED)
async def add_my_interest(
    data: StudentInterestCreate,
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    acad_profile = await profile_service.get_student_academic_profile_by_user(db, current_user.id)
    return await profile_service.add_student_interest(db, acad_profile.id, data)


@router.delete("/me/interests/{interest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_interest(
    interest_id: str,
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    acad_profile = await profile_service.get_student_academic_profile_by_user(db, current_user.id)
    await profile_service.delete_student_interest(db, interest_id, acad_profile.id)


# =========================================================================
# 5. Student Projects
# =========================================================================

@router.get("/me/projects", response_model=List[StudentProjectResponse])
async def list_my_projects(
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    acad_profile = await profile_service.get_student_academic_profile_by_user(db, current_user.id)
    projects = await profile_service.list_student_projects(db, acad_profile.id)
    return [
        StudentProjectResponse(
            id=p.id,
            student_profile_id=p.student_profile_id,
            title=p.title,
            description=p.description,
            project_type=p.project_type,
            status=p.status,
            start_date=p.start_date,
            end_date=p.end_date,
            repository_url=p.repository_url,
            demo_url=p.demo_url,
            documentation_url=p.documentation_url,
            technologies=p.technologies,
            team_or_individual=p.team_or_individual,
            role=p.role,
            outcomes=p.outcomes,
            is_verified=p.is_verified,
            verified_by_user_id=p.verified_by_user_id,
            skill_ids=[ps.skill_catalog_id for ps in p.project_skills] if p.project_skills else [],
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in projects
    ]


@router.post("/me/projects", response_model=StudentProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_my_project(
    data: StudentProjectCreate,
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    acad_profile = await profile_service.get_student_academic_profile_by_user(db, current_user.id)
    p = await profile_service.add_student_project(db, acad_profile.id, data)
    return StudentProjectResponse(
        id=p.id,
        student_profile_id=p.student_profile_id,
        title=p.title,
        description=p.description,
        project_type=p.project_type,
        status=p.status,
        start_date=p.start_date,
        end_date=p.end_date,
        repository_url=p.repository_url,
        demo_url=p.demo_url,
        documentation_url=p.documentation_url,
        technologies=p.technologies,
        team_or_individual=p.team_or_individual,
        role=p.role,
        outcomes=p.outcomes,
        is_verified=p.is_verified,
        verified_by_user_id=p.verified_by_user_id,
        skill_ids=[ps.skill_catalog_id for ps in p.project_skills] if p.project_skills else [],
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.patch("/me/projects/{project_id}", response_model=StudentProjectResponse)
async def update_my_project(
    project_id: str,
    data: StudentProjectUpdate,
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    acad_profile = await profile_service.get_student_academic_profile_by_user(db, current_user.id)
    p = await profile_service.update_student_project(db, project_id, acad_profile.id, data)
    return StudentProjectResponse(
        id=p.id,
        student_profile_id=p.student_profile_id,
        title=p.title,
        description=p.description,
        project_type=p.project_type,
        status=p.status,
        start_date=p.start_date,
        end_date=p.end_date,
        repository_url=p.repository_url,
        demo_url=p.demo_url,
        documentation_url=p.documentation_url,
        technologies=p.technologies,
        team_or_individual=p.team_or_individual,
        role=p.role,
        outcomes=p.outcomes,
        is_verified=p.is_verified,
        verified_by_user_id=p.verified_by_user_id,
        skill_ids=[ps.skill_catalog_id for ps in p.project_skills] if p.project_skills else [],
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.delete("/me/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_project(
    project_id: str,
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    acad_profile = await profile_service.get_student_academic_profile_by_user(db, current_user.id)
    await profile_service.delete_student_project(db, project_id, acad_profile.id)


@router.post("/projects/{project_id}/verify", response_model=StudentProjectResponse)
async def verify_project(
    project_id: str,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Faculty or Admin verifies a student project."""
    p = await profile_service.verify_student_project(db, project_id, current_user)
    return StudentProjectResponse(
        id=p.id,
        student_profile_id=p.student_profile_id,
        title=p.title,
        description=p.description,
        project_type=p.project_type,
        status=p.status,
        start_date=p.start_date,
        end_date=p.end_date,
        repository_url=p.repository_url,
        demo_url=p.demo_url,
        documentation_url=p.documentation_url,
        technologies=p.technologies,
        team_or_individual=p.team_or_individual,
        role=p.role,
        outcomes=p.outcomes,
        is_verified=p.is_verified,
        verified_by_user_id=p.verified_by_user_id,
        skill_ids=[],
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


# =========================================================================
# 6. Certifications & Achievements
# =========================================================================

@router.get("/me/certifications", response_model=List[StudentCertificationResponse])
async def list_my_certifications(
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    acad_profile = await profile_service.get_student_academic_profile_by_user(db, current_user.id)
    return await profile_service.list_student_certifications(db, acad_profile.id)


@router.post("/me/certifications", response_model=StudentCertificationResponse, status_code=status.HTTP_201_CREATED)
async def add_my_certification(
    data: StudentCertificationCreate,
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    acad_profile = await profile_service.get_student_academic_profile_by_user(db, current_user.id)
    return await profile_service.add_student_certification(db, acad_profile.id, data)


@router.post("/certifications/{cert_id}/verify", response_model=StudentCertificationResponse)
async def verify_certification(
    cert_id: str,
    data: StudentCertificationVerifyRequest,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Faculty or Admin verifies or rejects a certification with notes."""
    return await profile_service.verify_student_certification(db, cert_id, data, current_user)


@router.delete("/me/certifications/{cert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_certification(
    cert_id: str,
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    acad_profile = await profile_service.get_student_academic_profile_by_user(db, current_user.id)
    await profile_service.delete_student_certification(db, cert_id, acad_profile.id)


@router.get("/me/achievements", response_model=List[StudentAchievementResponse])
async def list_my_achievements(
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    acad_profile = await profile_service.get_student_academic_profile_by_user(db, current_user.id)
    return await profile_service.list_student_achievements(db, acad_profile.id)


@router.post("/me/achievements", response_model=StudentAchievementResponse, status_code=status.HTTP_201_CREATED)
async def add_my_achievement(
    data: StudentAchievementCreate,
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    acad_profile = await profile_service.get_student_academic_profile_by_user(db, current_user.id)
    return await profile_service.add_student_achievement(db, acad_profile.id, data)


@router.post("/achievements/{achievement_id}/verify", response_model=StudentAchievementResponse)
async def verify_achievement(
    achievement_id: str,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await profile_service.verify_student_achievement(db, achievement_id, current_user)


@router.delete("/me/achievements/{achievement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_achievement(
    achievement_id: str,
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    acad_profile = await profile_service.get_student_academic_profile_by_user(db, current_user.id)
    await profile_service.delete_student_achievement(db, achievement_id, acad_profile.id)


# =========================================================================
# 7. Portfolio & Resume
# =========================================================================

@router.get("/me/portfolio", response_model=StudentPortfolioResponse)
async def get_my_portfolio(
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    acad_profile = await profile_service.get_student_academic_profile_by_user(db, current_user.id)
    return await profile_service.get_or_create_student_portfolio(db, acad_profile.id)


@router.patch("/me/portfolio", response_model=StudentPortfolioResponse)
async def update_my_portfolio(
    data: StudentPortfolioUpdate,
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    acad_profile = await profile_service.get_student_academic_profile_by_user(db, current_user.id)
    return await profile_service.update_student_portfolio(db, acad_profile.id, data)


@router.get("/me/resume", response_model=StudentResumeResponse)
async def get_my_resume(
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    acad_profile = await profile_service.get_student_academic_profile_by_user(db, current_user.id)
    return await profile_service.get_or_create_student_resume(db, acad_profile.id)


@router.patch("/me/resume", response_model=StudentResumeResponse)
async def update_my_resume(
    data: StudentResumeUpdate,
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    acad_profile = await profile_service.get_student_academic_profile_by_user(db, current_user.id)
    return await profile_service.update_student_resume(db, acad_profile.id, data)
