"""REST API endpoints for Faculty Profiles, Assigned Offerings & Students."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, require_roles
from app.core.security import UserRole
from app.domains.identity.models import User
from app.domains.profiles.service import profile_service
from app.domains.profiles.schemas import (
    TeacherProfileDetailUpdate,
    TeacherProfileDetailResponse,
    FacultyDashboardOverview,
)

router = APIRouter(prefix="/faculty", tags=["Faculty & Teaching Context"])


@router.get("/me", response_model=TeacherProfileDetailResponse)
async def get_my_faculty_profile(
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the authenticated faculty's extended profile details."""
    teacher_prof = await profile_service.get_teacher_academic_profile_by_user(db, current_user.id)
    return await profile_service.get_or_create_teacher_detail(db, teacher_prof.id)


@router.patch("/me", response_model=TeacherProfileDetailResponse)
async def update_my_faculty_profile(
    data: TeacherProfileDetailUpdate,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD)),
    db: AsyncSession = Depends(get_db),
):
    """Update authenticated faculty's professional profile."""
    teacher_prof = await profile_service.get_teacher_academic_profile_by_user(db, current_user.id)
    return await profile_service.update_teacher_detail(db, teacher_prof.id, data)


@router.get("/me/overview", response_model=FacultyDashboardOverview)
async def get_my_faculty_overview(
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD)),
    db: AsyncSession = Depends(get_db),
):
    """Deterministic dashboard overview for authenticated faculty member."""
    return await profile_service.get_faculty_dashboard_overview(db, current_user.id)


@router.get("/me/offerings")
async def get_my_assigned_offerings(
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD)),
    db: AsyncSession = Depends(get_db),
):
    """Fetch assigned course offerings from Domain 2 TeachingAssignment."""
    teacher_prof = await profile_service.get_teacher_academic_profile_by_user(db, current_user.id)
    offerings = await profile_service.get_teacher_assigned_offerings(db, teacher_prof.id)
    return [
        {
            "offering_id": o.id,
            "course_id": o.course_id,
            "course_code": o.course.code if o.course else None,
            "course_title": o.course.title if o.course else None,
            "section_name": o.section.name if o.section else None,
            "semester_name": o.semester.label if o.semester else None,
            "academic_year": o.academic_year.name if o.academic_year else None,
            "status": o.status,
        }
        for o in offerings
    ]


@router.get("/me/students")
async def get_my_assigned_students(
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD)),
    db: AsyncSession = Depends(get_db),
):
    """Fetch unique students enrolled in the teacher's authorized course offerings."""
    teacher_prof = await profile_service.get_teacher_academic_profile_by_user(db, current_user.id)
    students = await profile_service.get_teacher_assigned_students(db, teacher_prof.id)
    return [
        {
            "student_profile_id": s.id,
            "enrollment_number": s.enrollment_number,
            "program_name": s.program.name if s.program else None,
            "batch_name": s.batch.label if s.batch else None,
            "section_name": s.current_section.name if s.current_section else None,
            "academic_status": s.academic_status,
        }
        for s in students
    ]
