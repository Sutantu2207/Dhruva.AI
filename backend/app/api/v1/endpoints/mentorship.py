"""REST API endpoints for Mentorship Relations, Cohort Groups & Private Notes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, require_roles
from app.core.security import UserRole
from app.domains.identity.models import User
from app.domains.profiles.service import profile_service
from app.domains.profiles.schemas import (
    MentorshipRelationCreate,
    MentorshipRelationResponse,
    MentorGroupCreate,
    MentorGroupAddStudentRequest,
    MentorGroupResponse,
    MentorNoteCreate,
    MentorNoteUpdate,
    MentorNoteResponse,
)

router = APIRouter(prefix="/mentorship", tags=["Mentorship & Cohorts"])


@router.get("/me", response_model=List[MentorshipRelationResponse])
async def get_my_mentees(
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.MENTOR, UserRole.HOD)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all active student mentorship relations assigned to the authenticated mentor."""
    assignments = await profile_service.list_mentor_assignments(db, current_user.id)
    return [
        MentorshipRelationResponse(
            id=a.id,
            institution_id=a.institution_id,
            mentor_user_id=a.mentor_user_id,
            student_profile_id=a.student_profile_id,
            start_date=a.start_date,
            end_date=a.end_date,
            status=a.status,
            assignment_source=a.assignment_source,
            created_at=a.created_at,
            updated_at=a.updated_at,
            student_name=None,
            student_enrollment_number=a.student_profile.enrollment_number if a.student_profile else None,
            mentor_name=a.mentor_user.display_name if a.mentor_user else None,
        )
        for a in assignments
    ]


@router.post("/assignments", response_model=MentorshipRelationResponse, status_code=status.HTTP_201_CREATED)
async def assign_mentor_to_student(
    data: MentorshipRelationCreate,
    current_user: User = Depends(require_roles(UserRole.INSTITUTION_ADMIN, UserRole.HOD, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Assign an individual mentor to a student."""
    rel = await profile_service.assign_mentor(db, data, current_user)
    return MentorshipRelationResponse(
        id=rel.id,
        institution_id=rel.institution_id,
        mentor_user_id=rel.mentor_user_id,
        student_profile_id=rel.student_profile_id,
        start_date=rel.start_date,
        end_date=rel.end_date,
        status=rel.status,
        assignment_source=rel.assignment_source,
        created_at=rel.created_at,
        updated_at=rel.updated_at,
    )


@router.post("/groups", response_model=MentorGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_mentor_group(
    data: MentorGroupCreate,
    current_user: User = Depends(require_roles(UserRole.INSTITUTION_ADMIN, UserRole.HOD, UserRole.SUPER_ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Create a mentor cohort group."""
    grp = await profile_service.create_mentor_group(db, data, current_user)
    return MentorGroupResponse(
        id=grp.id,
        institution_id=grp.institution_id,
        department_id=grp.department_id,
        mentor_user_id=grp.mentor_user_id,
        name=grp.name,
        description=grp.description,
        status=grp.status,
        member_count=0,
        created_at=grp.created_at,
        updated_at=grp.updated_at,
    )


@router.post("/groups/{group_id}/members", status_code=status.HTTP_201_CREATED)
async def add_student_to_group(
    group_id: str,
    data: MentorGroupAddStudentRequest,
    current_user: User = Depends(require_roles(UserRole.INSTITUTION_ADMIN, UserRole.HOD, UserRole.SUPER_ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Add a student to an existing mentor cohort."""
    await profile_service.add_student_to_mentor_group(db, group_id, data.student_profile_id)
    return {"status": "success", "message": "Student added to mentor group"}


@router.delete("/groups/{group_id}/members/{student_profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_student_from_group(
    group_id: str,
    student_profile_id: str,
    current_user: User = Depends(require_roles(UserRole.INSTITUTION_ADMIN, UserRole.HOD, UserRole.SUPER_ADMIN, UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Remove a student from a mentor cohort."""
    await profile_service.remove_student_from_mentor_group(db, group_id, student_profile_id)


# =========================================================================
# Mentor Notes (Permission & Privacy Controlled)
# =========================================================================

@router.get("/students/{student_profile_id}/notes", response_model=List[MentorNoteResponse])
async def list_mentor_notes_for_student(
    student_profile_id: str,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.MENTOR, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Fetch structured mentor notes. Strictly inaccessible to students; scoped to mentors."""
    notes = await profile_service.list_mentor_notes(db, student_profile_id, current_user)
    return notes


@router.post("/notes", response_model=MentorNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_mentor_note(
    data: MentorNoteCreate,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.MENTOR, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Record an auditable mentor observation note."""
    return await profile_service.add_mentor_note(db, data, current_user)
