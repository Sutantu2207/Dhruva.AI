"""Permission and Scope Resolver for Domain 11 AI interactions."""

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.domains.identity.models import User
from app.core.security import UserRole
from app.domains.academic.models import (
    StudentAcademicProfile,
    TeacherAcademicProfile,
    TeachingAssignment,
    CourseOffering,
)


class AIContextResolver:
    """Resolves authenticated identity, institutional hierarchy, and authorized domain context."""

    @staticmethod
    async def resolve_user_context(
        db: AsyncSession,
        user: User,
    ) -> Dict[str, Any]:
        """Synthesizes verified scope parameters for the user from authoritative database tables."""
        context: Dict[str, Any] = {
            "user_id": user.id,
            "role": user.role,
            "institution_id": user.institution_id,
            "first_name": user.first_name,
            "display_name": user.display_name,
        }

        if user.role == UserRole.STUDENT:
            stmt = select(StudentAcademicProfile).where(StudentAcademicProfile.user_id == user.id)
            res = await db.execute(stmt)
            profile = res.scalar_one_or_none()
            if profile:
                context["student_profile_id"] = profile.id
                context["program_id"] = profile.program_id
                context["batch_id"] = profile.batch_id
                context["enrollment_number"] = profile.enrollment_number
                context["institution_id"] = profile.institution_id

        elif user.role in [UserRole.TEACHER, UserRole.HOD]:
            stmt = select(TeacherAcademicProfile).where(TeacherAcademicProfile.user_id == user.id)
            res = await db.execute(stmt)
            profile = res.scalar_one_or_none()
            if profile:
                context["teacher_profile_id"] = profile.id
                context["department_id"] = profile.department_id
                context["institution_id"] = profile.institution_id

                # Load assigned course offerings
                t_stmt = select(TeachingAssignment.course_offering_id).where(
                    TeachingAssignment.teacher_profile_id == profile.id
                )
                t_res = await db.execute(t_stmt)
                context["assigned_offering_ids"] = list(t_res.scalars().all())

        return context
