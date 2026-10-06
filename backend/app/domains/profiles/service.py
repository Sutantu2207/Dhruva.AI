"""Domain 3: Student & Faculty Management, Mentorship & Profiles Service.

Provides complete business logic, RBAC, isolation, validation, and dashboard aggregations.
"""

from datetime import datetime, timezone, date
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy import select, func, and_, or_, distinct
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import UserRole
from app.domains.identity.models import User
from app.domains.academic.models import (
    Institution,
    Department,
    Program,
    Batch,
    Section,
    Course,
    CourseOffering,
    StudentAcademicProfile,
    TeacherAcademicProfile,
    StudentEnrollment,
    TeachingAssignment,
)
from app.domains.catalog.models import (
    SkillCatalog,
    CareerCatalog,
    AcademicDiscipline,
)
from app.domains.profiles.models import (
    StudentProfileDetail,
    StudentAcademicStatusHistory,
    StudentSkill,
    StudentInterest,
    StudentCareerGoal,
    StudentProject,
    StudentProjectSkill,
    StudentCertification,
    StudentAchievement,
    StudentPortfolio,
    StudentResume,
    TeacherProfileDetail,
    MentorshipRelation,
    MentorGroup,
    MentorGroupMember,
    MentorNote,
    StudentIntervention,
    OnboardingImportJob,
)
from app.domains.profiles.completion import calculate_profile_completion, ProfileCompletionReport
from app.domains.profiles.audit import record_audit_log
from app.domains.profiles.schemas import (
    StudentProfileDetailUpdate,
    StudentAcademicStatusChangeRequest,
    StudentSkillCreate,
    StudentSkillUpdate,
    StudentInterestCreate,
    StudentCareerGoalCreate,
    StudentCareerGoalUpdate,
    StudentProjectCreate,
    StudentProjectUpdate,
    StudentCertificationCreate,
    StudentCertificationUpdate,
    StudentCertificationVerifyRequest,
    StudentAchievementCreate,
    StudentAchievementUpdate,
    StudentPortfolioUpdate,
    StudentResumeUpdate,
    TeacherProfileDetailUpdate,
    MentorshipRelationCreate,
    MentorGroupCreate,
    MentorNoteCreate,
    MentorNoteUpdate,
    StudentInterventionCreate,
    StudentInterventionUpdate,
    StudentDashboardOverview,
    FacultyDashboardOverview,
    AdminInstitutionOverview,
)


class ProfileService:
    """Service layer for student, faculty, mentorship, and profile operations."""

    # =========================================================================
    # 1. Student Academic Profile & Biographical Details
    # =========================================================================

    async def get_student_academic_profile(
        self, db: AsyncSession, student_profile_id: str
    ) -> StudentAcademicProfile:
        stmt = (
            select(StudentAcademicProfile)
            .options(
                joinedload(StudentAcademicProfile.institution),
                joinedload(StudentAcademicProfile.program),
                joinedload(StudentAcademicProfile.batch),
                joinedload(StudentAcademicProfile.current_section),
            )
            .where(StudentAcademicProfile.id == student_profile_id)
        )
        res = await db.execute(stmt)
        profile = res.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student academic profile not found.")
        return profile

    async def get_student_academic_profile_by_user(
        self, db: AsyncSession, user_id: str
    ) -> StudentAcademicProfile:
        stmt = (
            select(StudentAcademicProfile)
            .options(
                joinedload(StudentAcademicProfile.institution),
                joinedload(StudentAcademicProfile.program),
                joinedload(StudentAcademicProfile.batch),
                joinedload(StudentAcademicProfile.current_section),
            )
            .where(StudentAcademicProfile.user_id == user_id)
        )
        res = await db.execute(stmt)
        profile = res.scalar_one_or_none()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student academic profile not found for this user account.",
            )
        return profile

    async def get_or_create_student_detail(
        self, db: AsyncSession, student_profile_id: str
    ) -> StudentProfileDetail:
        stmt = select(StudentProfileDetail).where(StudentProfileDetail.student_profile_id == student_profile_id)
        res = await db.execute(stmt)
        detail = res.scalar_one_or_none()
        if not detail:
            detail = StudentProfileDetail(student_profile_id=student_profile_id)
            db.add(detail)
            await db.flush()
        return detail

    async def update_student_detail(
        self,
        db: AsyncSession,
        student_profile_id: str,
        data: StudentProfileDetailUpdate,
        actor_user: User,
    ) -> StudentProfileDetail:
        detail = await self.get_or_create_student_detail(db, student_profile_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(detail, field, value)
        detail.updated_at = datetime.now(timezone.utc)

        await record_audit_log(
            db=db,
            actor_user_id=actor_user.id,
            action="update_student_profile_detail",
            resource_type="student_profile_details",
            resource_id=detail.id,
            institution_id=actor_user.institution_id,
        )
        await db.commit()
        await db.refresh(detail)
        return detail

    async def change_student_academic_status(
        self,
        db: AsyncSession,
        student_profile_id: str,
        data: StudentAcademicStatusChangeRequest,
        actor_user: User,
    ) -> StudentAcademicProfile:
        profile = await self.get_student_academic_profile(db, student_profile_id)
        old_status = profile.academic_status

        allowed_statuses = {
            "active", "on_leave", "suspended", "graduated", "withdrawn",
            "transferred", "completed", "inactive"
        }
        if data.new_status not in allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid academic status. Allowed: {list(allowed_statuses)}",
            )

        profile.academic_status = data.new_status
        profile.updated_at = datetime.now(timezone.utc)

        # Record auditable history
        hist = StudentAcademicStatusHistory(
            student_profile_id=student_profile_id,
            old_status=old_status,
            new_status=data.new_status,
            effective_from=data.effective_from,
            effective_to=data.effective_to,
            reason=data.reason,
            changed_by_user_id=actor_user.id,
        )
        db.add(hist)

        await record_audit_log(
            db=db,
            actor_user_id=actor_user.id,
            action="change_student_academic_status",
            resource_type="student_academic_profiles",
            resource_id=profile.id,
            institution_id=profile.institution_id,
            metadata_payload={
                "old_status": old_status,
                "new_status": data.new_status,
                "reason": data.reason,
            }
        )
        await db.commit()
        await db.refresh(profile)
        return profile

    async def get_student_status_history(
        self, db: AsyncSession, student_profile_id: str
    ) -> List[StudentAcademicStatusHistory]:
        stmt = (
            select(StudentAcademicStatusHistory)
            .where(StudentAcademicStatusHistory.student_profile_id == student_profile_id)
            .order_by(StudentAcademicStatusHistory.created_at.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    # =========================================================================
    # 2. Student Skills
    # =========================================================================

    async def list_student_skills(
        self, db: AsyncSession, student_profile_id: str
    ) -> List[StudentSkill]:
        stmt = (
            select(StudentSkill)
            .options(joinedload(StudentSkill.skill_catalog))
            .where(StudentSkill.student_profile_id == student_profile_id)
            .order_by(StudentSkill.created_at.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def add_student_skill(
        self,
        db: AsyncSession,
        student_profile_id: str,
        data: StudentSkillCreate,
        actor_user: User,
    ) -> StudentSkill:
        # Validate skill exists in SkillCatalog
        stmt_cat = select(SkillCatalog).where(SkillCatalog.id == data.skill_catalog_id)
        cat_skill = (await db.execute(stmt_cat)).scalar_one_or_none()
        if not cat_skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill with ID '{data.skill_catalog_id}' not found in canonical SkillCatalog.",
            )

        # Check unique constraint
        stmt_exist = select(StudentSkill).where(
            StudentSkill.student_profile_id == student_profile_id,
            StudentSkill.skill_catalog_id == data.skill_catalog_id,
        )
        if (await db.execute(stmt_exist)).scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Student already has this skill mapped in their profile.",
            )

        # Deterministic verification check: claiming a skill NEVER auto-verifies it
        is_verified = False
        verified_by = None
        if data.source in ("faculty_verified", "course_verified") and actor_user.role in (
            UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN
        ):
            is_verified = True
            verified_by = actor_user.id

        new_skill = StudentSkill(
            student_profile_id=student_profile_id,
            skill_catalog_id=data.skill_catalog_id,
            proficiency=data.proficiency,
            source=data.source,
            is_verified=is_verified,
            verified_by_user_id=verified_by,
        )
        db.add(new_skill)
        await db.commit()
        await db.refresh(new_skill)
        return new_skill

    async def update_student_skill(
        self,
        db: AsyncSession,
        skill_id: str,
        data: StudentSkillUpdate,
        actor_user: User,
    ) -> StudentSkill:
        stmt = select(StudentSkill).where(StudentSkill.id == skill_id)
        skill = (await db.execute(stmt)).scalar_one_or_none()
        if not skill:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student skill not found.")

        if data.proficiency is not None:
            skill.proficiency = data.proficiency
        if data.source is not None:
            skill.source = data.source
        if data.is_verified is not None:
            # Only teachers or admins can directly alter verification
            if actor_user.role in (UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN):
                skill.is_verified = data.is_verified
                skill.verified_by_user_id = actor_user.id if data.is_verified else None
        skill.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(skill)
        return skill

    async def delete_student_skill(
        self, db: AsyncSession, skill_id: str, student_profile_id: str
    ) -> None:
        stmt = select(StudentSkill).where(
            StudentSkill.id == skill_id,
            StudentSkill.student_profile_id == student_profile_id,
        )
        skill = (await db.execute(stmt)).scalar_one_or_none()
        if not skill:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student skill not found.")
        await db.delete(skill)
        await db.commit()

    # =========================================================================
    # 3. Student Interests & Career Goals
    # =========================================================================

    async def list_student_interests(
        self, db: AsyncSession, student_profile_id: str
    ) -> List[StudentInterest]:
        stmt = (
            select(StudentInterest)
            .where(StudentInterest.student_profile_id == student_profile_id)
            .order_by(StudentInterest.created_at.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def add_student_interest(
        self,
        db: AsyncSession,
        student_profile_id: str,
        data: StudentInterestCreate,
    ) -> StudentInterest:
        if data.discipline_id:
            stmt_disc = select(AcademicDiscipline).where(AcademicDiscipline.id == data.discipline_id)
            if not (await db.execute(stmt_disc)).scalar_one_or_none():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referenced AcademicDiscipline not found.")
        if data.career_catalog_id:
            stmt_car = select(CareerCatalog).where(CareerCatalog.id == data.career_catalog_id)
            if not (await db.execute(stmt_car)).scalar_one_or_none():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referenced CareerCatalog not found.")

        interest = StudentInterest(
            student_profile_id=student_profile_id,
            interest_title=data.interest_title.strip(),
            discipline_id=data.discipline_id,
            career_catalog_id=data.career_catalog_id,
            notes=data.notes,
        )
        db.add(interest)
        await db.commit()
        await db.refresh(interest)
        return interest

    async def delete_student_interest(
        self, db: AsyncSession, interest_id: str, student_profile_id: str
    ) -> None:
        stmt = select(StudentInterest).where(
            StudentInterest.id == interest_id,
            StudentInterest.student_profile_id == student_profile_id,
        )
        interest = (await db.execute(stmt)).scalar_one_or_none()
        if not interest:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student interest not found.")
        await db.delete(interest)
        await db.commit()

    async def list_student_career_goals(
        self, db: AsyncSession, student_profile_id: str
    ) -> List[StudentCareerGoal]:
        stmt = (
            select(StudentCareerGoal)
            .options(joinedload(StudentCareerGoal.career_catalog))
            .where(StudentCareerGoal.student_profile_id == student_profile_id)
            .order_by(StudentCareerGoal.priority.asc(), StudentCareerGoal.created_at.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def add_student_career_goal(
        self,
        db: AsyncSession,
        student_profile_id: str,
        data: StudentCareerGoalCreate,
    ) -> StudentCareerGoal:
        # Canonical validation
        stmt_car = select(CareerCatalog).where(CareerCatalog.id == data.career_catalog_id)
        if not (await db.execute(stmt_car)).scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Career ID '{data.career_catalog_id}' not found in canonical CareerCatalog.",
            )

        stmt_exist = select(StudentCareerGoal).where(
            StudentCareerGoal.student_profile_id == student_profile_id,
            StudentCareerGoal.career_catalog_id == data.career_catalog_id,
        )
        if (await db.execute(stmt_exist)).scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Student already has this target career goal mapped in their profile.",
            )

        goal = StudentCareerGoal(
            student_profile_id=student_profile_id,
            career_catalog_id=data.career_catalog_id,
            priority=data.priority,
            short_term_goals=data.short_term_goals,
            long_term_goals=data.long_term_goals,
            target_industry=data.target_industry,
            preferred_locations=data.preferred_locations,
            target_organizations=data.target_organizations,
        )
        db.add(goal)
        await db.commit()
        await db.refresh(goal)
        return goal

    async def update_student_career_goal(
        self,
        db: AsyncSession,
        goal_id: str,
        student_profile_id: str,
        data: StudentCareerGoalUpdate,
    ) -> StudentCareerGoal:
        stmt = select(StudentCareerGoal).where(
            StudentCareerGoal.id == goal_id,
            StudentCareerGoal.student_profile_id == student_profile_id,
        )
        goal = (await db.execute(stmt)).scalar_one_or_none()
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Career goal not found.")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(goal, field, value)
        goal.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(goal)
        return goal

    async def delete_student_career_goal(
        self, db: AsyncSession, goal_id: str, student_profile_id: str
    ) -> None:
        stmt = select(StudentCareerGoal).where(
            StudentCareerGoal.id == goal_id,
            StudentCareerGoal.student_profile_id == student_profile_id,
        )
        goal = (await db.execute(stmt)).scalar_one_or_none()
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Career goal not found.")
        await db.delete(goal)
        await db.commit()

    # =========================================================================
    # 4. Student Projects
    # =========================================================================

    async def list_student_projects(
        self, db: AsyncSession, student_profile_id: str
    ) -> List[StudentProject]:
        stmt = (
            select(StudentProject)
            .options(selectinload(StudentProject.project_skills))
            .where(StudentProject.student_profile_id == student_profile_id)
            .order_by(StudentProject.created_at.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def add_student_project(
        self,
        db: AsyncSession,
        student_profile_id: str,
        data: StudentProjectCreate,
    ) -> StudentProject:
        project = StudentProject(
            student_profile_id=student_profile_id,
            title=data.title.strip(),
            description=data.description,
            project_type=data.project_type,
            status=data.status,
            start_date=data.start_date,
            end_date=data.end_date,
            repository_url=data.repository_url,
            demo_url=data.demo_url,
            documentation_url=data.documentation_url,
            technologies=data.technologies,
            team_or_individual=data.team_or_individual,
            role=data.role,
            outcomes=data.outcomes,
            is_verified=False,  # Never auto-verified on creation
        )
        db.add(project)
        await db.flush()

        # Connect skill catalog IDs if provided
        if data.skill_catalog_ids:
            for skill_id in data.skill_catalog_ids:
                stmt_sk = select(SkillCatalog).where(SkillCatalog.id == skill_id)
                if (await db.execute(stmt_sk)).scalar_one_or_none():
                    ps = StudentProjectSkill(project_id=project.id, skill_catalog_id=skill_id)
                    db.add(ps)

        await db.commit()
        await db.refresh(project)
        return project

    async def update_student_project(
        self,
        db: AsyncSession,
        project_id: str,
        student_profile_id: str,
        data: StudentProjectUpdate,
    ) -> StudentProject:
        stmt = (
            select(StudentProject)
            .options(selectinload(StudentProject.project_skills))
            .where(
                StudentProject.id == project_id,
                StudentProject.student_profile_id == student_profile_id,
            )
        )
        project = (await db.execute(stmt)).scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

        for field, value in data.model_dump(exclude={"skill_catalog_ids"}, exclude_unset=True).items():
            setattr(project, field, value)

        if data.skill_catalog_ids is not None:
            # Clear old and map new
            stmt_del = select(StudentProjectSkill).where(StudentProjectSkill.project_id == project.id)
            old_skills = (await db.execute(stmt_del)).scalars().all()
            for os in old_skills:
                await db.delete(os)

            for skill_id in data.skill_catalog_ids:
                stmt_sk = select(SkillCatalog).where(SkillCatalog.id == skill_id)
                if (await db.execute(stmt_sk)).scalar_one_or_none():
                    ps = StudentProjectSkill(project_id=project.id, skill_catalog_id=skill_id)
                    db.add(ps)

        project.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(project)
        return project

    async def delete_student_project(
        self, db: AsyncSession, project_id: str, student_profile_id: str
    ) -> None:
        stmt = select(StudentProject).where(
            StudentProject.id == project_id,
            StudentProject.student_profile_id == student_profile_id,
        )
        project = (await db.execute(stmt)).scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
        await db.delete(project)
        await db.commit()

    async def verify_student_project(
        self,
        db: AsyncSession,
        project_id: str,
        actor_user: User,
    ) -> StudentProject:
        stmt = select(StudentProject).where(StudentProject.id == project_id)
        project = (await db.execute(stmt)).scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

        project.is_verified = True
        project.verified_by_user_id = actor_user.id
        project.updated_at = datetime.now(timezone.utc)

        await record_audit_log(
            db=db,
            actor_user_id=actor_user.id,
            action="verify_student_project",
            resource_type="student_projects",
            resource_id=project.id,
            institution_id=actor_user.institution_id,
        )
        await db.commit()
        await db.refresh(project)
        return project

    # =========================================================================
    # 5. Certifications & Achievements
    # =========================================================================

    async def list_student_certifications(
        self, db: AsyncSession, student_profile_id: str
    ) -> List[StudentCertification]:
        stmt = (
            select(StudentCertification)
            .where(StudentCertification.student_profile_id == student_profile_id)
            .order_by(StudentCertification.created_at.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def add_student_certification(
        self,
        db: AsyncSession,
        student_profile_id: str,
        data: StudentCertificationCreate,
    ) -> StudentCertification:
        cert = StudentCertification(
            student_profile_id=student_profile_id,
            title=data.title.strip(),
            issuer=data.issuer.strip(),
            credential_id=data.credential_id,
            issue_date=data.issue_date,
            expiry_date=data.expiry_date,
            credential_url=data.credential_url,
            document_reference=data.document_reference,
            status="unverified",  # Never auto-verified on creation
        )
        db.add(cert)
        await db.commit()
        await db.refresh(cert)
        return cert

    async def verify_student_certification(
        self,
        db: AsyncSession,
        cert_id: str,
        data: StudentCertificationVerifyRequest,
        actor_user: User,
    ) -> StudentCertification:
        stmt = select(StudentCertification).where(StudentCertification.id == cert_id)
        cert = (await db.execute(stmt)).scalar_one_or_none()
        if not cert:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certification not found.")

        cert.status = data.status
        cert.verification_notes = data.verification_notes
        cert.verified_by_user_id = actor_user.id
        cert.updated_at = datetime.now(timezone.utc)

        await record_audit_log(
            db=db,
            actor_user_id=actor_user.id,
            action=f"certification_{data.status}",
            resource_type="student_certifications",
            resource_id=cert.id,
            institution_id=actor_user.institution_id,
            metadata_payload={"status": data.status, "notes": data.verification_notes},
        )
        await db.commit()
        await db.refresh(cert)
        return cert

    async def delete_student_certification(
        self, db: AsyncSession, cert_id: str, student_profile_id: str
    ) -> None:
        stmt = select(StudentCertification).where(
            StudentCertification.id == cert_id,
            StudentCertification.student_profile_id == student_profile_id,
        )
        cert = (await db.execute(stmt)).scalar_one_or_none()
        if not cert:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certification not found.")
        await db.delete(cert)
        await db.commit()

    async def list_student_achievements(
        self, db: AsyncSession, student_profile_id: str
    ) -> List[StudentAchievement]:
        stmt = (
            select(StudentAchievement)
            .where(StudentAchievement.student_profile_id == student_profile_id)
            .order_by(StudentAchievement.created_at.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def add_student_achievement(
        self,
        db: AsyncSession,
        student_profile_id: str,
        data: StudentAchievementCreate,
    ) -> StudentAchievement:
        ach = StudentAchievement(
            student_profile_id=student_profile_id,
            title=data.title.strip(),
            description=data.description,
            category=data.category,
            achievement_date=data.achievement_date,
            issuer_event=data.issuer_event,
            evidence_url=data.evidence_url,
            is_verified=False,
        )
        db.add(ach)
        await db.commit()
        await db.refresh(ach)
        return ach

    async def verify_student_achievement(
        self,
        db: AsyncSession,
        achievement_id: str,
        actor_user: User,
    ) -> StudentAchievement:
        stmt = select(StudentAchievement).where(StudentAchievement.id == achievement_id)
        ach = (await db.execute(stmt)).scalar_one_or_none()
        if not ach:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Achievement not found.")

        ach.is_verified = True
        ach.verified_by_user_id = actor_user.id
        ach.updated_at = datetime.now(timezone.utc)

        await record_audit_log(
            db=db,
            actor_user_id=actor_user.id,
            action="verify_student_achievement",
            resource_type="student_achievements",
            resource_id=ach.id,
            institution_id=actor_user.institution_id,
        )
        await db.commit()
        await db.refresh(ach)
        return ach

    async def delete_student_achievement(
        self, db: AsyncSession, achievement_id: str, student_profile_id: str
    ) -> None:
        stmt = select(StudentAchievement).where(
            StudentAchievement.id == achievement_id,
            StudentAchievement.student_profile_id == student_profile_id,
        )
        ach = (await db.execute(stmt)).scalar_one_or_none()
        if not ach:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Achievement not found.")
        await db.delete(ach)
        await db.commit()

    # =========================================================================
    # 6. Student Portfolio & Resume
    # =========================================================================

    async def get_or_create_student_portfolio(
        self, db: AsyncSession, student_profile_id: str
    ) -> StudentPortfolio:
        stmt = select(StudentPortfolio).where(StudentPortfolio.student_profile_id == student_profile_id)
        portfolio = (await db.execute(stmt)).scalar_one_or_none()
        if not portfolio:
            portfolio = StudentPortfolio(student_profile_id=student_profile_id)
            db.add(portfolio)
            await db.flush()
        return portfolio

    async def update_student_portfolio(
        self,
        db: AsyncSession,
        student_profile_id: str,
        data: StudentPortfolioUpdate,
    ) -> StudentPortfolio:
        portfolio = await self.get_or_create_student_portfolio(db, student_profile_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(portfolio, field, value)
        portfolio.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(portfolio)
        return portfolio

    async def get_or_create_student_resume(
        self, db: AsyncSession, student_profile_id: str
    ) -> StudentResume:
        stmt = select(StudentResume).where(StudentResume.student_profile_id == student_profile_id)
        resume = (await db.execute(stmt)).scalar_one_or_none()
        if not resume:
            resume = StudentResume(student_profile_id=student_profile_id)
            db.add(resume)
            await db.flush()
        return resume

    async def update_student_resume(
        self,
        db: AsyncSession,
        student_profile_id: str,
        data: StudentResumeUpdate,
    ) -> StudentResume:
        resume = await self.get_or_create_student_resume(db, student_profile_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(resume, field, value)
        resume.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(resume)
        return resume

    # =========================================================================
    # 7. Faculty Extended Profile & Assigned Teaching Context
    # =========================================================================

    async def get_teacher_academic_profile_by_user(
        self, db: AsyncSession, user_id: str
    ) -> TeacherAcademicProfile:
        stmt = (
            select(TeacherAcademicProfile)
            .options(
                joinedload(TeacherAcademicProfile.institution),
                joinedload(TeacherAcademicProfile.department),
            )
            .where(TeacherAcademicProfile.user_id == user_id)
        )
        profile = (await db.execute(stmt)).scalar_one_or_none()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher academic profile not found for this user account.",
            )
        return profile

    async def get_or_create_teacher_detail(
        self, db: AsyncSession, teacher_profile_id: str
    ) -> TeacherProfileDetail:
        stmt = select(TeacherProfileDetail).where(TeacherProfileDetail.teacher_profile_id == teacher_profile_id)
        detail = (await db.execute(stmt)).scalar_one_or_none()
        if not detail:
            detail = TeacherProfileDetail(teacher_profile_id=teacher_profile_id)
            db.add(detail)
            await db.flush()
        return detail

    async def update_teacher_detail(
        self,
        db: AsyncSession,
        teacher_profile_id: str,
        data: TeacherProfileDetailUpdate,
    ) -> TeacherProfileDetail:
        detail = await self.get_or_create_teacher_detail(db, teacher_profile_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(detail, field, value)
        detail.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(detail)
        return detail

    async def get_teacher_assigned_offerings(
        self, db: AsyncSession, teacher_profile_id: str
    ) -> List[CourseOffering]:
        """Fetches CourseOfferings where the teacher is assigned via TeachingAssignment."""
        stmt = (
            select(CourseOffering)
            .join(TeachingAssignment, TeachingAssignment.course_offering_id == CourseOffering.id)
            .options(
                joinedload(CourseOffering.course),
                joinedload(CourseOffering.section),
                joinedload(CourseOffering.semester),
                joinedload(CourseOffering.academic_year),
            )
            .where(TeachingAssignment.teacher_profile_id == teacher_profile_id)
            .distinct()
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def get_teacher_assigned_students(
        self, db: AsyncSession, teacher_profile_id: str
    ) -> List[StudentAcademicProfile]:
        """Fetches unique students enrolled in offerings taught by the teacher."""
        stmt = (
            select(StudentAcademicProfile)
            .join(StudentEnrollment, StudentEnrollment.student_profile_id == StudentAcademicProfile.id)
            .join(CourseOffering, CourseOffering.id == StudentEnrollment.course_offering_id)
            .join(TeachingAssignment, TeachingAssignment.course_offering_id == CourseOffering.id)
            .options(
                joinedload(StudentAcademicProfile.program),
                joinedload(StudentAcademicProfile.batch),
                joinedload(StudentAcademicProfile.current_section),
            )
            .where(
                TeachingAssignment.teacher_profile_id == teacher_profile_id,
                StudentEnrollment.enrollment_status == "enrolled",
            )
            .distinct()
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    # =========================================================================
    # 8. Mentorship System
    # =========================================================================

    async def assign_mentor(
        self,
        db: AsyncSession,
        data: MentorshipRelationCreate,
        actor_user: User,
    ) -> MentorshipRelation:
        student_prof = await self.get_student_academic_profile(db, data.student_profile_id)

        # Check mentor user exists
        stmt_m = select(User).where(User.id == data.mentor_user_id)
        mentor_user = (await db.execute(stmt_m)).scalar_one_or_none()
        if not mentor_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentor user not found.")

        # Ensure mentor belongs to same institution
        if mentor_user.institution_id and student_prof.institution_id:
            if mentor_user.institution_id != student_prof.institution_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot assign mentor from a different institution.",
                )

        # Check existing relation
        stmt_exist = select(MentorshipRelation).where(
            MentorshipRelation.mentor_user_id == data.mentor_user_id,
            MentorshipRelation.student_profile_id == data.student_profile_id,
        )
        if (await db.execute(stmt_exist)).scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Mentorship assignment already exists between this mentor and student.",
            )

        relation = MentorshipRelation(
            institution_id=student_prof.institution_id,
            mentor_user_id=data.mentor_user_id,
            student_profile_id=data.student_profile_id,
            start_date=data.start_date,
            assignment_source=data.assignment_source,
            status="active",
        )
        db.add(relation)

        await record_audit_log(
            db=db,
            actor_user_id=actor_user.id,
            action="assign_mentor",
            resource_type="mentorship_relations",
            resource_id=relation.id,
            institution_id=student_prof.institution_id,
        )
        await db.commit()
        await db.refresh(relation)
        return relation

    async def list_mentor_assignments(
        self, db: AsyncSession, mentor_user_id: str
    ) -> List[MentorshipRelation]:
        stmt = (
            select(MentorshipRelation)
            .options(
                joinedload(MentorshipRelation.student_profile).joinedload(StudentAcademicProfile.program),
                joinedload(MentorshipRelation.mentor_user),
            )
            .where(
                MentorshipRelation.mentor_user_id == mentor_user_id,
                MentorshipRelation.status == "active",
            )
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def get_student_assigned_mentor(
        self, db: AsyncSession, student_profile_id: str
    ) -> Optional[MentorshipRelation]:
        stmt = (
            select(MentorshipRelation)
            .options(joinedload(MentorshipRelation.mentor_user))
            .where(
                MentorshipRelation.student_profile_id == student_profile_id,
                MentorshipRelation.status == "active",
            )
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def create_mentor_group(
        self,
        db: AsyncSession,
        data: MentorGroupCreate,
        actor_user: User,
    ) -> MentorGroup:
        institution_id = actor_user.institution_id
        if not institution_id and actor_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Institution context required.")

        group = MentorGroup(
            institution_id=institution_id or "global",
            department_id=data.department_id,
            mentor_user_id=data.mentor_user_id,
            name=data.name.strip(),
            description=data.description,
            status="active",
        )
        db.add(group)
        await db.commit()
        await db.refresh(group)
        return group

    async def add_student_to_mentor_group(
        self,
        db: AsyncSession,
        group_id: str,
        student_profile_id: str,
    ) -> MentorGroupMember:
        stmt_grp = select(MentorGroup).where(MentorGroup.id == group_id)
        group = (await db.execute(stmt_grp)).scalar_one_or_none()
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentor group not found.")

        stmt_m = select(MentorGroupMember).where(
            MentorGroupMember.mentor_group_id == group_id,
            MentorGroupMember.student_profile_id == student_profile_id,
        )
        if (await db.execute(stmt_m)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student is already in this mentor group.")

        member = MentorGroupMember(
            mentor_group_id=group_id,
            student_profile_id=student_profile_id,
        )
        db.add(member)
        await db.commit()
        await db.refresh(member)
        return member

    async def remove_student_from_mentor_group(
        self, db: AsyncSession, group_id: str, student_profile_id: str
    ) -> None:
        stmt = select(MentorGroupMember).where(
            MentorGroupMember.mentor_group_id == group_id,
            MentorGroupMember.student_profile_id == student_profile_id,
        )
        member = (await db.execute(stmt)).scalar_one_or_none()
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group membership not found.")
        await db.delete(member)
        await db.commit()

    async def add_mentor_note(
        self,
        db: AsyncSession,
        data: MentorNoteCreate,
        mentor_user: User,
    ) -> MentorNote:
        student_prof = await self.get_student_academic_profile(db, data.student_profile_id)

        note = MentorNote(
            institution_id=student_prof.institution_id,
            mentor_user_id=mentor_user.id,
            student_profile_id=data.student_profile_id,
            content=data.content,
            visibility=data.visibility,
            follow_up_date=data.follow_up_date,
            status="open",
        )
        db.add(note)
        await db.commit()
        await db.refresh(note)
        return note

    async def list_mentor_notes(
        self,
        db: AsyncSession,
        student_profile_id: str,
        requesting_user: User,
    ) -> List[MentorNote]:
        """Permission-controlled retrieval of mentor notes.
        
        Strict Privacy:
        - Students NEVER see private_mentor notes.
        - Shared notes are visible to authorized faculty / admins only.
        """
        # If student themselves is querying, return empty or 403
        if requesting_user.role == UserRole.STUDENT:
            return []

        stmt = select(MentorNote).where(MentorNote.student_profile_id == student_profile_id)

        if requesting_user.role in (UserRole.TEACHER, UserRole.MENTOR):
            # Show notes authored by this mentor, OR notes marked shared_faculty
            stmt = stmt.where(
                or_(
                    MentorNote.mentor_user_id == requesting_user.id,
                    MentorNote.visibility == "shared_faculty",
                )
            )

        stmt = stmt.order_by(MentorNote.created_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    # =========================================================================
    # 9. Follow-Up / Intervention Foundation
    # =========================================================================

    async def create_intervention(
        self,
        db: AsyncSession,
        data: StudentInterventionCreate,
        actor_user: User,
    ) -> StudentIntervention:
        student_prof = await self.get_student_academic_profile(db, data.student_profile_id)

        intervention = StudentIntervention(
            institution_id=student_prof.institution_id,
            student_profile_id=data.student_profile_id,
            created_by_user_id=actor_user.id,
            category=data.category,
            priority=data.priority,
            status="open",
            reason=data.reason,
            action_plan=data.action_plan,
            follow_up_date=data.follow_up_date,
        )
        db.add(intervention)
        await db.flush()

        await record_audit_log(
            db=db,
            actor_user_id=actor_user.id,
            action="create_student_intervention",
            resource_type="student_interventions",
            resource_id=intervention.id,
            institution_id=student_prof.institution_id,
            metadata_payload={"category": data.category, "priority": data.priority},
        )
        await db.commit()
        await db.refresh(intervention)
        return intervention

    async def resolve_intervention(
        self,
        db: AsyncSession,
        intervention_id: str,
        resolution_notes: str,
        actor_user: User,
    ) -> StudentIntervention:
        stmt = select(StudentIntervention).where(StudentIntervention.id == intervention_id)
        intervention = (await db.execute(stmt)).scalar_one_or_none()
        if not intervention:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intervention not found.")

        intervention.status = "resolved"
        intervention.resolution_notes = resolution_notes
        intervention.resolved_by_user_id = actor_user.id
        intervention.updated_at = datetime.now(timezone.utc)

        await record_audit_log(
            db=db,
            actor_user_id=actor_user.id,
            action="resolve_student_intervention",
            resource_type="student_interventions",
            resource_id=intervention.id,
            institution_id=intervention.institution_id,
            metadata_payload={"resolution_notes": resolution_notes},
        )
        await db.commit()
        await db.refresh(intervention)
        return intervention

    async def list_interventions(
        self,
        db: AsyncSession,
        student_profile_id: Optional[str] = None,
        institution_id: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> List[StudentIntervention]:
        stmt = select(StudentIntervention)
        if student_profile_id:
            stmt = stmt.where(StudentIntervention.student_profile_id == student_profile_id)
        if institution_id:
            stmt = stmt.where(StudentIntervention.institution_id == institution_id)
        if status_filter:
            stmt = stmt.where(StudentIntervention.status == status_filter)
        stmt = stmt.order_by(StudentIntervention.created_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    # =========================================================================
    # 10. Real Aggregated Dashboard Overviews
    # =========================================================================

    async def get_student_dashboard_overview(
        self, db: AsyncSession, student_user_id: str
    ) -> StudentDashboardOverview:
        prof = await self.get_student_academic_profile_by_user(db, student_user_id)
        detail = await self.get_or_create_student_detail(db, prof.id)
        portfolio = (await db.execute(select(StudentPortfolio).where(StudentPortfolio.student_profile_id == prof.id))).scalar_one_or_none()
        resume = (await db.execute(select(StudentResume).where(StudentResume.student_profile_id == prof.id))).scalar_one_or_none()

        # Database counts
        skills_count = (await db.execute(select(func.count(StudentSkill.id)).where(StudentSkill.student_profile_id == prof.id))).scalar() or 0
        verified_skills_count = (await db.execute(select(func.count(StudentSkill.id)).where(StudentSkill.student_profile_id == prof.id, StudentSkill.is_verified == True))).scalar() or 0
        career_goals_count = (await db.execute(select(func.count(StudentCareerGoal.id)).where(StudentCareerGoal.student_profile_id == prof.id))).scalar() or 0
        interests_count = (await db.execute(select(func.count(StudentInterest.id)).where(StudentInterest.student_profile_id == prof.id))).scalar() or 0
        projects_count = (await db.execute(select(func.count(StudentProject.id)).where(StudentProject.student_profile_id == prof.id))).scalar() or 0
        certs_count = (await db.execute(select(func.count(StudentCertification.id)).where(StudentCertification.student_profile_id == prof.id))).scalar() or 0
        achievements_count = (await db.execute(select(func.count(StudentAchievement.id)).where(StudentAchievement.student_profile_id == prof.id))).scalar() or 0
        active_courses_count = (await db.execute(select(func.count(StudentEnrollment.id)).where(StudentEnrollment.student_profile_id == prof.id, StudentEnrollment.enrollment_status == "enrolled"))).scalar() or 0
        active_interventions_count = (await db.execute(select(func.count(StudentIntervention.id)).where(StudentIntervention.student_profile_id == prof.id, StudentIntervention.status == "open"))).scalar() or 0

        # Mentor relation
        mentor_rel = await self.get_student_assigned_mentor(db, prof.id)
        mentor_name = mentor_rel.mentor_user.display_name if mentor_rel and mentor_rel.mentor_user else None

        # Profile completion
        completion_rep = calculate_profile_completion(
            academic_profile=prof,
            profile_detail=detail,
            skills_count=skills_count,
            career_goals_count=career_goals_count,
            interests_count=interests_count,
            projects_count=projects_count,
            certifications_count=certs_count,
            portfolio=portfolio,
            resume=resume,
        )

        return StudentDashboardOverview(
            user_id=student_user_id,
            student_profile_id=prof.id,
            enrollment_number=prof.enrollment_number,
            academic_status=prof.academic_status,
            institution_name=prof.institution.name if prof.institution else "Institutional Affiliation",
            program_name=prof.program.name if prof.program else "Academic Program",
            batch_name=prof.batch.label if prof.batch else "Cohort Batch",
            section_name=prof.current_section.name if prof.current_section else None,
            completion_percentage=completion_rep.completion_percentage,
            completed_sections=completion_rep.completed_sections,
            missing_sections=completion_rep.missing_sections,
            active_courses_count=active_courses_count,
            total_skills_count=skills_count,
            verified_skills_count=verified_skills_count,
            projects_count=projects_count,
            certifications_count=certs_count,
            achievements_count=achievements_count,
            mentor_name=mentor_name,
            active_interventions_count=active_interventions_count,
        )

    async def get_faculty_dashboard_overview(
        self, db: AsyncSession, faculty_user_id: str
    ) -> FacultyDashboardOverview:
        prof = await self.get_teacher_academic_profile_by_user(db, faculty_user_id)
        assigned_offerings = await self.get_teacher_assigned_offerings(db, prof.id)
        assigned_students = await self.get_teacher_assigned_students(db, prof.id)

        mentees_count = (
            await db.execute(
                select(func.count(MentorshipRelation.id)).where(
                    MentorshipRelation.mentor_user_id == faculty_user_id,
                    MentorshipRelation.status == "active",
                )
            )
        ).scalar() or 0

        pending_follow_ups = (
            await db.execute(
                select(func.count(MentorNote.id)).where(
                    MentorNote.mentor_user_id == faculty_user_id,
                    MentorNote.status == "open",
                    MentorNote.follow_up_date <= date.today(),
                )
            )
        ).scalar() or 0

        return FacultyDashboardOverview(
            user_id=faculty_user_id,
            teacher_profile_id=prof.id,
            employee_id=prof.employee_id,
            designation=prof.designation,
            department_name=prof.department.name if prof.department else "Department",
            institution_name=prof.institution.name if prof.institution else "Institution",
            assigned_offerings_count=len(assigned_offerings),
            total_enrolled_students=len(assigned_students),
            assigned_mentees_count=mentees_count,
            pending_follow_ups_count=pending_follow_ups,
            profile_status=prof.status,
        )

    async def get_admin_institution_overview(
        self, db: AsyncSession, institution_id: str
    ) -> AdminInstitutionOverview:
        stmt_inst = select(Institution).where(Institution.id == institution_id)
        inst = (await db.execute(stmt_inst)).scalar_one_or_none()
        if not inst:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found.")

        total_students = (await db.execute(select(func.count(StudentAcademicProfile.id)).where(StudentAcademicProfile.institution_id == institution_id))).scalar() or 0
        total_faculty = (await db.execute(select(func.count(TeacherAcademicProfile.id)).where(TeacherAcademicProfile.institution_id == institution_id))).scalar() or 0
        active_programs = (await db.execute(select(func.count(Program.id)).join(Department, Department.id == Program.department_id).where(Department.institution_id == institution_id, Program.status == "active"))).scalar() or 0
        active_batches = (await db.execute(select(func.count(Batch.id)).join(Program, Program.id == Batch.program_id).join(Department, Department.id == Program.department_id).where(Department.institution_id == institution_id, Batch.status == "active"))).scalar() or 0
        total_sections = (await db.execute(select(func.count(Section.id)).join(Batch, Batch.id == Section.batch_id).join(Program, Program.id == Batch.program_id).join(Department, Department.id == Program.department_id).where(Department.institution_id == institution_id))).scalar() or 0
        total_courses = (await db.execute(select(func.count(Course.id)).where(Course.institution_id == institution_id, Course.status == "active"))).scalar() or 0

        # Status distribution
        status_stmt = select(StudentAcademicProfile.academic_status, func.count(StudentAcademicProfile.id)).where(StudentAcademicProfile.institution_id == institution_id).group_by(StudentAcademicProfile.academic_status)
        status_rows = (await db.execute(status_stmt)).all()
        status_distribution = {row[0]: row[1] for row in status_rows}

        pending_onboarding = (await db.execute(select(func.count(OnboardingImportJob.id)).where(OnboardingImportJob.institution_id == institution_id, OnboardingImportJob.status == "pending"))).scalar() or 0

        return AdminInstitutionOverview(
            institution_id=inst.id,
            institution_name=inst.name,
            total_students=total_students,
            total_faculty=total_faculty,
            active_programs=active_programs,
            active_batches=active_batches,
            total_sections=total_sections,
            total_courses=total_courses,
            status_distribution=status_distribution,
            pending_onboarding_jobs=pending_onboarding,
        )


profile_service = ProfileService()
