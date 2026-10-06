"""Business logic service for Domain 4: Course Delivery, Curriculum Structure & Learning Content Engine."""

from datetime import datetime, timezone
import json
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.core.security import UserRole
from app.domains.identity.models import User
from app.domains.academic.models import (
    Course,
    CourseOffering,
    Institution,
    Department,
    StudentAcademicProfile,
    TeacherAcademicProfile,
    StudentEnrollment,
    TeachingAssignment,
)
from app.domains.catalog.models import (
    CourseCatalog,
    SkillCatalog,
    AcademicDiscipline,
)
from app.domains.content.models import (
    CourseContent,
    CourseContentVersion,
    Curriculum,
    Module,
    Lesson,
    LessonContentBlock,
    LearningObjective,
    Concept,
    ConceptPrerequisite,
    LessonConcept,
    ConceptSkill,
    LessonSkill,
    CourseSkill,
    LearningResource,
    ResourceVersion,
    LessonResource,
    ContentReview,
    ContentReviewComment,
    LessonProgress,
    CourseProgress,
    StudentBookmark,
    StudentLearningNote,
)
from app.domains.content.schemas import (
    CourseContentCreate,
    CourseContentUpdate,
    CurriculumCreate,
    CurriculumUpdate,
    ModuleCreate,
    ModuleUpdate,
    LessonCreate,
    LessonUpdate,
    ContentBlockCreate,
    ContentBlockUpdate,
    LearningObjectiveCreate,
    ConceptCreate,
    ConceptUpdate,
    ConceptPrerequisiteCreate,
    ConceptSkillCreate,
    LessonConceptCreate,
    LessonSkillCreate,
    CourseSkillCreate,
    ResourceCreate,
    ResourceUpdate,
    LessonResourceAttach,
    ContentReviewSubmitRequest,
    ContentReviewDecisionRequest,
    ContentReviewCommentCreate,
    LessonProgressUpdateRequest,
    BookmarkCreate,
    LearningNoteCreate,
    LearningNoteUpdate,
)
from app.domains.content.security import validate_content_block, sanitize_html
from app.domains.audit.service import record_audit_event


class ContentService:
    """Service providing core course authoring, curriculum delivery, and progress tracking."""

    # =====================================================================
    # Authorization Helpers
    # =====================================================================

    @staticmethod
    async def get_student_profile(db: AsyncSession, user_id: str) -> StudentAcademicProfile:
        stmt = select(StudentAcademicProfile).where(StudentAcademicProfile.user_id == user_id)
        res = await db.execute(stmt)
        profile = res.scalar_one_or_none()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student academic profile not found for user",
            )
        return profile

    @staticmethod
    async def get_teacher_profile(db: AsyncSession, user_id: str) -> Optional[TeacherAcademicProfile]:
        stmt = select(TeacherAcademicProfile).where(TeacherAcademicProfile.user_id == user_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def verify_faculty_access(
        db: AsyncSession,
        user: User,
        course_id: str,
        institution_id: str,
    ) -> None:
        """Verifies faculty or admin permission to manage content for a course."""
        if user.role == UserRole.SUPER_ADMIN:
            return

        if user.role == UserRole.INSTITUTION_ADMIN:
            if user.institution_id != institution_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cross-institution content management forbidden",
                )
            return

        # Fetch course to check department
        stmt = select(Course).where(Course.id == course_id)
        res = await db.execute(stmt)
        course = res.scalar_one_or_none()
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

        if course.institution_id != user.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cross-institution content management forbidden",
            )

        if user.role == UserRole.HOD:
            # HOD can manage courses in their department
            teacher_prof = await ContentService.get_teacher_profile(db, user.id)
            if teacher_prof and teacher_prof.department_id == course.department_id:
                return
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="HOD cannot manage courses outside assigned department",
            )

        if user.role == UserRole.TEACHER:
            teacher_prof = await ContentService.get_teacher_profile(db, user.id)
            if not teacher_prof:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher profile not found")

            # Check if teacher has teaching assignment in any offering for this course
            assign_stmt = (
                select(TeachingAssignment)
                .join(CourseOffering, TeachingAssignment.course_offering_id == CourseOffering.id)
                .where(
                    and_(
                        TeachingAssignment.teacher_profile_id == teacher_prof.id,
                        CourseOffering.course_id == course_id,
                    )
                )
            )
            assign_res = await db.execute(assign_stmt)
            if assign_res.scalar_one_or_none():
                return

            # Or if course is in their department and they are course owner
            content_stmt = select(CourseContent).where(
                and_(
                    CourseContent.course_id == course_id,
                    or_(CourseContent.author_id == user.id, CourseContent.owner_id == user.id),
                )
            )
            content_res = await db.execute(content_stmt)
            if content_res.scalar_one_or_none():
                return

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teacher not assigned to this course or authorized as content owner",
            )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role not authorized for content management",
        )

    # =====================================================================
    # 1. Course Content Management
    # =====================================================================

    @staticmethod
    async def create_course_content(
        db: AsyncSession,
        user: User,
        data: CourseContentCreate,
    ) -> CourseContent:
        course_stmt = select(Course).where(Course.id == data.course_id)
        course_res = await db.execute(course_stmt)
        course = course_res.scalar_one_or_none()
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

        await ContentService.verify_faculty_access(db, user, course.id, course.institution_id)

        # Check if content already exists for course
        existing_stmt = select(CourseContent).where(CourseContent.course_id == course.id)
        existing_res = await db.execute(existing_stmt)
        if existing_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Course content container already exists for this course. Use updates.",
            )

        content = CourseContent(
            institution_id=course.institution_id,
            course_id=course.id,
            course_catalog_id=data.course_catalog_id,
            title=data.title,
            short_description=data.short_description,
            detailed_description=data.detailed_description,
            learning_objectives=data.learning_objectives,
            target_audience=data.target_audience,
            difficulty=data.difficulty,
            estimated_duration=data.estimated_duration,
            language=data.language,
            status="draft",
            version=1,
            author_id=user.id,
            owner_id=user.id,
        )
        db.add(content)
        await db.flush()

        # Create default empty curriculum container
        curriculum = Curriculum(
            course_content_id=content.id,
            title=f"{content.title} Curriculum",
            description=content.short_description,
            ordering_type="sequential",
            status="active",
        )
        db.add(curriculum)
        await db.flush()

        record_audit_event(
            actor_id=user.id,
            actor_role=user.role,
            event_type="course_content_created",
            resource_type="course_content",
            resource_id=content.id,
            payload={"course_id": course.id, "title": content.title},
        )
        await db.commit()
        await db.refresh(content)
        return content

    @staticmethod
    async def get_course_content_by_id(
        db: AsyncSession,
        content_id: str,
        user: Optional[User] = None,
    ) -> CourseContent:
        stmt = (
            select(CourseContent)
            .where(CourseContent.id == content_id)
            .options(
                selectinload(CourseContent.curriculum)
                .selectinload(Curriculum.modules)
                .selectinload(Module.lessons)
                .selectinload(Lesson.content_blocks)
            )
        )
        res = await db.execute(stmt)
        content = res.scalar_one_or_none()
        if not content:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course content not found")

        # Authorization check: If unpublished, only authorized faculty/admin can view
        if content.status != "published":
            if not user or user.role == UserRole.STUDENT:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Students cannot access unpublished learning content",
                )
            if user.role != UserRole.SUPER_ADMIN and user.institution_id != content.institution_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cross-institution content access forbidden",
                )

        return content

    @staticmethod
    async def update_course_content(
        db: AsyncSession,
        content_id: str,
        user: User,
        data: CourseContentUpdate,
    ) -> CourseContent:
        content = await ContentService.get_course_content_by_id(db, content_id, user)
        await ContentService.verify_faculty_access(db, user, content.course_id, content.institution_id)

        # Published content protection: cannot edit published content directly in-place without versioning/review
        if content.status == "published" and data.status != "archived":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Published content is protected. Create a new revision or submit updates via review.",
            )

        update_data = data.model_dump(exclude_unset=True)
        for key, val in update_data.items():
            setattr(content, key, val)

        record_audit_event(
            actor_id=user.id,
            actor_role=user.role,
            event_type="course_content_updated",
            resource_type="course_content",
            resource_id=content.id,
            payload={"updated_fields": list(update_data.keys())},
        )
        await db.commit()
        await db.refresh(content)
        return content

    # =====================================================================
    # 2. Curriculum, Modules & Lessons
    # =====================================================================

    @staticmethod
    async def get_curriculum(db: AsyncSession, course_id: str, user: Optional[User] = None) -> Curriculum:
        content_stmt = select(CourseContent).where(CourseContent.course_id == course_id)
        content_res = await db.execute(content_stmt)
        content = content_res.scalar_one_or_none()
        if not content:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No content configured for course")

        # Authorization: Students only see published content
        if content.status != "published":
            if not user or user.role == UserRole.STUDENT:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Students cannot access unpublished curriculum",
                )

        stmt = (
            select(Curriculum)
            .where(Curriculum.course_content_id == content.id)
            .options(
                selectinload(Curriculum.modules)
                .selectinload(Module.lessons)
                .selectinload(Lesson.content_blocks)
            )
        )
        res = await db.execute(stmt)
        curriculum = res.scalar_one_or_none()
        if not curriculum:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum not found")
        return curriculum

    @staticmethod
    async def create_module(
        db: AsyncSession,
        curriculum_id: str,
        user: User,
        data: ModuleCreate,
    ) -> Module:
        curr_stmt = (
            select(Curriculum)
            .where(Curriculum.id == curriculum_id)
            .options(joinedload(Curriculum.course_content))
        )
        curr_res = await db.execute(curr_stmt)
        curriculum = curr_res.scalar_one_or_none()
        if not curriculum:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum not found")

        content = curriculum.course_content
        await ContentService.verify_faculty_access(db, user, content.course_id, content.institution_id)

        # Compute next order_index deterministically if not explicitly provided
        count_stmt = select(func.count(Module.id)).where(Module.curriculum_id == curriculum_id)
        count_res = await db.execute(count_stmt)
        current_count = count_res.scalar_one()

        order_idx = data.order_index if data.order_index > 0 else current_count

        module = Module(
            curriculum_id=curriculum_id,
            title=data.title,
            slug=data.slug,
            description=data.description,
            order_index=order_idx,
            estimated_minutes=data.estimated_minutes,
            learning_objectives=data.learning_objectives,
            prerequisites=data.prerequisites,
            status=data.status,
        )
        db.add(module)
        await db.commit()

        # Reload with lessons eagerly loaded to prevent lazy-load MissingGreenlet
        reload_stmt = (
            select(Module)
            .where(Module.id == module.id)
            .options(selectinload(Module.lessons))
        )
        res = await db.execute(reload_stmt)
        return res.scalar_one()

    @staticmethod
    async def reorder_modules(
        db: AsyncSession,
        curriculum_id: str,
        user: User,
        module_ids: List[str],
    ) -> List[Module]:
        curr_stmt = (
            select(Curriculum)
            .where(Curriculum.id == curriculum_id)
            .options(joinedload(Curriculum.course_content))
        )
        curr_res = await db.execute(curr_stmt)
        curriculum = curr_res.scalar_one_or_none()
        if not curriculum:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum not found")

        content = curriculum.course_content
        await ContentService.verify_faculty_access(db, user, content.course_id, content.institution_id)

        # Two-pass update to avoid temporary unique constraint collisions
        for idx, mod_id in enumerate(module_ids):
            stmt = select(Module).where(and_(Module.id == mod_id, Module.curriculum_id == curriculum_id))
            res = await db.execute(stmt)
            mod = res.scalar_one_or_none()
            if mod:
                mod.order_index = -(idx + 1000)
        await db.flush()

        for idx, mod_id in enumerate(module_ids):
            stmt = select(Module).where(and_(Module.id == mod_id, Module.curriculum_id == curriculum_id))
            res = await db.execute(stmt)
            mod = res.scalar_one_or_none()
            if mod:
                mod.order_index = idx

        await db.commit()
        # Return updated ordered list with eager lessons
        result_stmt = (
            select(Module)
            .where(Module.curriculum_id == curriculum_id)
            .options(selectinload(Module.lessons))
            .order_by(Module.order_index.asc())
        )
        res = await db.execute(result_stmt)
        return list(res.scalars().all())

    @staticmethod
    async def create_lesson(
        db: AsyncSession,
        module_id: str,
        user: User,
        data: LessonCreate,
    ) -> Lesson:
        mod_stmt = (
            select(Module)
            .where(Module.id == module_id)
            .options(
                joinedload(Module.curriculum).joinedload(Curriculum.course_content)
            )
        )
        mod_res = await db.execute(mod_stmt)
        module = mod_res.scalar_one_or_none()
        if not module:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")

        content = module.curriculum.course_content
        await ContentService.verify_faculty_access(db, user, content.course_id, content.institution_id)

        count_stmt = select(func.count(Lesson.id)).where(Lesson.module_id == module_id)
        count_res = await db.execute(count_stmt)
        current_count = count_res.scalar_one()

        order_idx = data.order_index if data.order_index > 0 else current_count

        lesson = Lesson(
            module_id=module_id,
            title=data.title,
            slug=data.slug,
            description=data.description,
            lesson_type=data.lesson_type,
            order_index=order_idx,
            estimated_minutes=data.estimated_minutes,
            learning_objectives=data.learning_objectives,
            prerequisites=data.prerequisites,
            status=data.status,
            is_required=data.is_required,
        )
        db.add(lesson)
        await db.commit()

        reload_stmt = (
            select(Lesson)
            .where(Lesson.id == lesson.id)
            .options(selectinload(Lesson.content_blocks))
        )
        res = await db.execute(reload_stmt)
        return res.scalar_one()

    @staticmethod
    async def reorder_lessons(
        db: AsyncSession,
        module_id: str,
        user: User,
        lesson_ids: List[str],
    ) -> List[Lesson]:
        mod_stmt = (
            select(Module)
            .where(Module.id == module_id)
            .options(
                joinedload(Module.curriculum).joinedload(Curriculum.course_content)
            )
        )
        mod_res = await db.execute(mod_stmt)
        module = mod_res.scalar_one_or_none()
        if not module:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")

        content = module.curriculum.course_content
        await ContentService.verify_faculty_access(db, user, content.course_id, content.institution_id)

        # Two-pass update to avoid temporary unique constraint collisions
        for idx, les_id in enumerate(lesson_ids):
            stmt = select(Lesson).where(and_(Lesson.id == les_id, Lesson.module_id == module_id))
            res = await db.execute(stmt)
            les = res.scalar_one_or_none()
            if les:
                les.order_index = -(idx + 1000)
        await db.flush()

        for idx, les_id in enumerate(lesson_ids):
            stmt = select(Lesson).where(and_(Lesson.id == les_id, Lesson.module_id == module_id))
            res = await db.execute(stmt)
            les = res.scalar_one_or_none()
            if les:
                les.order_index = idx

        await db.commit()
        result_stmt = (
            select(Lesson)
            .where(Lesson.module_id == module_id)
            .options(selectinload(Lesson.content_blocks))
            .order_by(Lesson.order_index.asc())
        )
        res = await db.execute(result_stmt)
        return list(res.scalars().all())

    # =====================================================================
    # 3. Lesson Content Blocks & Security Sanitization
    # =====================================================================

    @staticmethod
    async def add_content_block(
        db: AsyncSession,
        lesson_id: str,
        user: User,
        data: ContentBlockCreate,
    ) -> LessonContentBlock:
        les_stmt = (
            select(Lesson)
            .where(Lesson.id == lesson_id)
            .options(
                joinedload(Lesson.module)
                .joinedload(Module.curriculum)
                .joinedload(Curriculum.course_content)
            )
        )
        les_res = await db.execute(les_stmt)
        lesson = les_res.scalar_one_or_none()
        if not lesson:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

        content = lesson.module.curriculum.course_content
        await ContentService.verify_faculty_access(db, user, content.course_id, content.institution_id)

        # XSS / Protocol Sanitization
        sanitized_content, validated_url = validate_content_block(
            block_type=data.block_type,
            content=data.content,
            media_url=data.media_url,
        )

        count_stmt = select(func.count(LessonContentBlock.id)).where(LessonContentBlock.lesson_id == lesson_id)
        count_res = await db.execute(count_stmt)
        order_idx = count_res.scalar_one()

        block = LessonContentBlock(
            lesson_id=lesson_id,
            block_type=data.block_type,
            order_index=order_idx,
            content=sanitized_content,
            media_url=validated_url,
            block_metadata=data.block_metadata,
        )
        db.add(block)
        await db.commit()
        await db.refresh(block)
        return block

    # =====================================================================
    # 4. Concepts, Graph Relations & Skills
    # =====================================================================

    @staticmethod
    async def create_concept(db: AsyncSession, user: User, data: ConceptCreate) -> Concept:
        # Check unique name and slug
        stmt = select(Concept).where(or_(Concept.name == data.name, Concept.slug == data.slug))
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Concept with name '{data.name}' or slug '{data.slug}' already exists",
            )

        concept = Concept(
            name=data.name,
            slug=data.slug,
            description=data.description,
            discipline_id=data.discipline_id,
            difficulty=data.difficulty,
            parent_concept_id=data.parent_concept_id,
            status="active",
        )
        db.add(concept)
        await db.commit()
        await db.refresh(concept)
        return concept

    @staticmethod
    async def add_concept_prerequisite(
        db: AsyncSession,
        concept_id: str,
        user: User,
        data: ConceptPrerequisiteCreate,
    ) -> ConceptPrerequisite:
        if concept_id == data.prerequisite_concept_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A concept cannot be a prerequisite of itself",
            )

        prereq = ConceptPrerequisite(
            concept_id=concept_id,
            prerequisite_concept_id=data.prerequisite_concept_id,
            relationship_type=data.relationship_type,
        )
        db.add(prereq)
        await db.commit()
        await db.refresh(prereq)
        return prereq

    @staticmethod
    async def map_concept_skill(
        db: AsyncSession,
        concept_id: str,
        user: User,
        data: ConceptSkillCreate,
    ) -> ConceptSkill:
        # Ensure SkillCatalog exists
        skill_stmt = select(SkillCatalog).where(SkillCatalog.id == data.skill_id)
        skill_res = await db.execute(skill_stmt)
        if not skill_res.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill catalog entry not found")

        mapping = ConceptSkill(
            concept_id=concept_id,
            skill_id=data.skill_id,
            weight=data.weight,
            expected_level=data.expected_level,
        )
        db.add(mapping)
        await db.commit()
        await db.refresh(mapping)
        return mapping

    @staticmethod
    async def map_lesson_concept(
        db: AsyncSession,
        lesson_id: str,
        user: User,
        data: LessonConceptCreate,
    ) -> LessonConcept:
        mapping = LessonConcept(
            lesson_id=lesson_id,
            concept_id=data.concept_id,
            importance=data.importance,
        )
        db.add(mapping)
        await db.commit()
        await db.refresh(mapping)
        return mapping

    @staticmethod
    async def map_lesson_skill(
        db: AsyncSession,
        lesson_id: str,
        user: User,
        data: LessonSkillCreate,
    ) -> LessonSkill:
        mapping = LessonSkill(
            lesson_id=lesson_id,
            skill_id=data.skill_id,
            importance=data.importance,
            expected_level=data.expected_level,
            evidence_type=data.evidence_type,
        )
        db.add(mapping)
        await db.commit()
        await db.refresh(mapping)
        return mapping

    @staticmethod
    async def map_course_skill(
        db: AsyncSession,
        course_content_id: str,
        user: User,
        data: CourseSkillCreate,
    ) -> CourseSkill:
        mapping = CourseSkill(
            course_content_id=course_content_id,
            skill_id=data.skill_id,
            importance=data.importance,
            expected_level=data.expected_level,
        )
        db.add(mapping)
        await db.commit()
        await db.refresh(mapping)
        return mapping

    # =====================================================================
    # 5. Resources & Attachments
    # =====================================================================

    @staticmethod
    async def create_resource(
        db: AsyncSession,
        user: User,
        data: ResourceCreate,
    ) -> LearningResource:
        resource = LearningResource(
            institution_id=user.institution_id if user.role != UserRole.SUPER_ADMIN else None,
            title=data.title,
            description=data.description,
            resource_type=data.resource_type,
            url=data.url,
            provider=data.provider or "local",
            duration_seconds=data.duration_seconds,
            access_level=data.access_level,
            copyright_license=data.copyright_license,
            status="active",
            current_version=1,
            created_by=user.id,
        )
        db.add(resource)
        await db.commit()
        await db.refresh(resource)
        return resource

    @staticmethod
    async def attach_resource_to_lesson(
        db: AsyncSession,
        lesson_id: str,
        user: User,
        data: LessonResourceAttach,
    ) -> LessonResource:
        attachment = LessonResource(
            lesson_id=lesson_id,
            resource_id=data.resource_id,
            order_index=data.order_index,
            is_mandatory=data.is_mandatory,
        )
        db.add(attachment)
        await db.commit()
        await db.refresh(attachment)
        return attachment

    # =====================================================================
    # 6. Content Review & Publishing Workflow
    # =====================================================================

    @staticmethod
    async def submit_content_for_review(
        db: AsyncSession,
        content_id: str,
        user: User,
        data: ContentReviewSubmitRequest,
    ) -> ContentReview:
        content = await ContentService.get_course_content_by_id(db, content_id, user)
        await ContentService.verify_faculty_access(db, user, content.course_id, content.institution_id)

        if content.status == "published":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Content is already published")

        # Validate minimum completeness: must have at least 1 module and 1 lesson
        if not content.curriculum or not content.curriculum.modules:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot submit empty curriculum for review. Add at least one module and lesson.",
            )

        has_lesson = any(len(m.lessons) > 0 for m in content.curriculum.modules)
        if not has_lesson:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Curriculum must contain at least one lesson before submitting for review.",
            )

        content.status = "in_review"

        review = ContentReview(
            course_content_id=content_id,
            submitted_by=user.id,
            status="submitted",
            review_notes=data.review_notes,
        )
        db.add(review)
        await db.flush()

        record_audit_event(
            actor_id=user.id,
            actor_role=user.role,
            event_type="content_submitted_for_review",
            resource_type="course_content",
            resource_id=content.id,
            payload={"review_id": review.id},
        )
        await db.commit()
        reload_stmt = (
            select(ContentReview)
            .where(ContentReview.id == review.id)
            .options(selectinload(ContentReview.comments))
        )
        r_res = await db.execute(reload_stmt)
        return r_res.scalar_one()

    @staticmethod
    async def decide_content_review(
        db: AsyncSession,
        review_id: str,
        user: User,
        data: ContentReviewDecisionRequest,
    ) -> ContentReview:
        stmt = (
            select(ContentReview)
            .where(ContentReview.id == review_id)
            .options(
                joinedload(ContentReview.course_content)
                .selectinload(CourseContent.curriculum)
                .selectinload(Curriculum.modules)
                .selectinload(Module.lessons),
                selectinload(ContentReview.comments),
            )
        )
        res = await db.execute(stmt)
        review = res.scalar_one_or_none()
        if not review:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content review not found")

        content = review.course_content

        # Reviewer authorization: HOD, Institution Admin, or Super Admin
        if user.role not in {UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only HODs, Institution Admins, or Super Admins can approve or request changes on content",
            )

        if user.role != UserRole.SUPER_ADMIN and user.institution_id != content.institution_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-institution review forbidden")

        review.reviewed_by = user.id
        review.reviewed_at = datetime.now(timezone.utc)

        if data.decision == "approve":
            review.status = "approved"
            content.status = "published"

            # Create immutable CourseContentVersion snapshot
            version_num = content.version
            snapshot = {
                "course_content_id": content.id,
                "title": content.title,
                "version": version_num,
                "modules": [
                    {
                        "id": m.id,
                        "title": m.title,
                        "order_index": m.order_index,
                        "lessons": [
                            {"id": l.id, "title": l.title, "order_index": l.order_index}
                            for l in m.lessons
                        ],
                    }
                    for m in (content.curriculum.modules if content.curriculum else [])
                ],
            }

            content_ver = CourseContentVersion(
                course_content_id=content.id,
                version_number=version_num,
                status="published",
                created_by=user.id,
                published_at=datetime.now(timezone.utc),
                change_summary=data.review_notes or f"Published version {version_num}",
                snapshot_data=snapshot,
            )
            db.add(content_ver)
            content.version = version_num + 1  # Prepare next version number for future revisions

            record_audit_event(
                actor_id=user.id,
                actor_role=user.role,
                event_type="content_published",
                resource_type="course_content",
                resource_id=content.id,
                payload={"version_number": version_num, "review_id": review.id},
            )
        else:
            review.status = "changes_requested"
            content.status = "draft"
            if data.review_notes:
                comment = ContentReviewComment(
                    review_id=review.id,
                    author_id=user.id,
                    comment=data.review_notes,
                )
                db.add(comment)

            record_audit_event(
                actor_id=user.id,
                actor_role=user.role,
                event_type="content_changes_requested",
                resource_type="course_content",
                resource_id=content.id,
                payload={"review_id": review.id},
            )

        await db.commit()
        reload_stmt = (
            select(ContentReview)
            .where(ContentReview.id == review_id)
            .options(selectinload(ContentReview.comments))
        )
        r_res = await db.execute(reload_stmt)
        return r_res.scalar_one()

    # =====================================================================
    # 7. Student Delivery & Deterministic Learning Progress
    # =====================================================================

    @staticmethod
    async def verify_student_course_enrollment(
        db: AsyncSession,
        user: User,
        course_offering_id: str,
    ) -> Tuple[StudentAcademicProfile, CourseOffering, CourseContent]:
        """Validates that student belongs to institution, is enrolled in offering, and content is published."""
        profile = await ContentService.get_student_profile(db, user.id)

        # Check course offering
        offering_stmt = (
            select(CourseOffering)
            .where(CourseOffering.id == course_offering_id)
            .options(joinedload(CourseOffering.course))
        )
        offering_res = await db.execute(offering_stmt)
        offering = offering_res.scalar_one_or_none()
        if not offering:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course offering not found")

        # Institutional isolation
        if offering.course.institution_id != profile.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Student cannot access courses from another institution",
            )

        # Verify active enrollment
        enroll_stmt = select(StudentEnrollment).where(
            and_(
                StudentEnrollment.student_profile_id == profile.id,
                StudentEnrollment.course_offering_id == course_offering_id,
                StudentEnrollment.enrollment_status == "enrolled",
            )
        )
        enroll_res = await db.execute(enroll_stmt)
        if not enroll_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Student is not actively enrolled in this course offering",
            )

        # Fetch published course content
        content_stmt = select(CourseContent).where(
            and_(
                CourseContent.course_id == offering.course_id,
                CourseContent.status == "published",
            )
        )
        content_res = await db.execute(content_stmt)
        content = content_res.scalar_one_or_none()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Published course learning content not available for this course",
            )

        return profile, offering, content

    @staticmethod
    async def start_lesson(
        db: AsyncSession,
        user: User,
        lesson_id: str,
        course_offering_id: str,
    ) -> LessonProgress:
        profile, offering, content = await ContentService.verify_student_course_enrollment(
            db, user, course_offering_id
        )

        prog_stmt = select(LessonProgress).where(
            and_(
                LessonProgress.student_profile_id == profile.id,
                LessonProgress.lesson_id == lesson_id,
                LessonProgress.course_offering_id == course_offering_id,
            )
        )
        prog_res = await db.execute(prog_stmt)
        progress = prog_res.scalar_one_or_none()

        now = datetime.now(timezone.utc)
        if not progress:
            progress = LessonProgress(
                student_profile_id=profile.id,
                lesson_id=lesson_id,
                course_offering_id=course_offering_id,
                content_version=content.version,
                status="in_progress",
                completion_percentage=0.0,
                time_spent_seconds=0,
                started_at=now,
                last_accessed_at=now,
            )
            db.add(progress)
        else:
            progress.last_accessed_at = now
            if progress.status == "not_started":
                progress.status = "in_progress"
                progress.started_at = now

        await db.commit()
        await db.refresh(progress)
        return progress

    @staticmethod
    async def update_lesson_progress(
        db: AsyncSession,
        user: User,
        lesson_id: str,
        data: LessonProgressUpdateRequest,
    ) -> LessonProgress:
        profile, offering, content = await ContentService.verify_student_course_enrollment(
            db, user, data.course_offering_id
        )

        prog_stmt = select(LessonProgress).where(
            and_(
                LessonProgress.student_profile_id == profile.id,
                LessonProgress.lesson_id == lesson_id,
                LessonProgress.course_offering_id == data.course_offering_id,
            )
        )
        prog_res = await db.execute(prog_stmt)
        progress = prog_res.scalar_one_or_none()
        now = datetime.now(timezone.utc)

        if not progress:
            progress = LessonProgress(
                student_profile_id=profile.id,
                lesson_id=lesson_id,
                course_offering_id=data.course_offering_id,
                content_version=content.version,
                status="in_progress",
                completion_percentage=data.completion_percentage,
                time_spent_seconds=data.time_spent_seconds,
                started_at=now,
                last_accessed_at=now,
            )
            db.add(progress)
        else:
            progress.time_spent_seconds += data.time_spent_seconds
            progress.completion_percentage = max(progress.completion_percentage, data.completion_percentage)
            progress.last_accessed_at = now

        await db.commit()
        await db.refresh(progress)
        return progress

    @staticmethod
    async def complete_lesson(
        db: AsyncSession,
        user: User,
        lesson_id: str,
        course_offering_id: str,
        time_spent_seconds: int = 0,
    ) -> Tuple[LessonProgress, CourseProgress]:
        """Marks a lesson completed and deterministically recalculates course roll-up progress."""
        profile, offering, content = await ContentService.verify_student_course_enrollment(
            db, user, course_offering_id
        )

        now = datetime.now(timezone.utc)
        prog_stmt = select(LessonProgress).where(
            and_(
                LessonProgress.student_profile_id == profile.id,
                LessonProgress.lesson_id == lesson_id,
                LessonProgress.course_offering_id == course_offering_id,
            )
        )
        prog_res = await db.execute(prog_stmt)
        progress = prog_res.scalar_one_or_none()

        if not progress:
            progress = LessonProgress(
                student_profile_id=profile.id,
                lesson_id=lesson_id,
                course_offering_id=course_offering_id,
                content_version=content.version,
                status="completed",
                completion_percentage=100.0,
                time_spent_seconds=time_spent_seconds,
                started_at=now,
                completed_at=now,
                last_accessed_at=now,
            )
            db.add(progress)
        else:
            progress.status = "completed"
            progress.completion_percentage = 100.0
            progress.time_spent_seconds += time_spent_seconds
            if not progress.completed_at:
                progress.completed_at = now
            progress.last_accessed_at = now

        await db.flush()

        # Deterministic Course Progress Recalculation
        course_prog = await ContentService._recalculate_course_progress(
            db, profile.id, offering.id, content.id, content.version
        )

        await db.commit()
        await db.refresh(progress)
        await db.refresh(course_prog)
        return progress, course_prog

    @staticmethod
    async def _recalculate_course_progress(
        db: AsyncSession,
        student_profile_id: str,
        offering_id: str,
        content_id: str,
        content_version: int,
    ) -> CourseProgress:
        # 1. Fetch all required lessons in this course content
        req_lessons_stmt = (
            select(Lesson.id, Lesson.module_id)
            .join(Module, Lesson.module_id == Module.id)
            .join(Curriculum, Module.curriculum_id == Curriculum.id)
            .where(
                and_(
                    Curriculum.course_content_id == content_id,
                    Lesson.is_required == True,
                    Lesson.status == "active",
                )
            )
        )
        req_res = await db.execute(req_lessons_stmt)
        req_rows = req_res.all()
        total_required_lessons = len(req_rows)

        # Total modules count
        mod_count_stmt = (
            select(func.count(Module.id))
            .join(Curriculum, Module.curriculum_id == Curriculum.id)
            .where(Curriculum.course_content_id == content_id)
        )
        mod_res = await db.execute(mod_count_stmt)
        total_modules = mod_res.scalar_one()

        # 2. Fetch completed required lessons for this student
        completed_stmt = (
            select(LessonProgress.lesson_id)
            .where(
                and_(
                    LessonProgress.student_profile_id == student_profile_id,
                    LessonProgress.course_offering_id == offering_id,
                    LessonProgress.status == "completed",
                )
            )
        )
        comp_res = await db.execute(completed_stmt)
        completed_ids = set(comp_res.scalars().all())

        completed_required_count = sum(1 for row in req_rows if row[0] in completed_ids)

        percentage = 0.0
        if total_required_lessons > 0:
            percentage = round((completed_required_count / total_required_lessons) * 100.0, 2)
        elif total_modules > 0:
            percentage = 100.0

        is_completed = (total_required_lessons > 0 and completed_required_count >= total_required_lessons)

        # 3. Calculate completed modules
        completed_modules = 0
        module_lessons_map: Dict[str, List[str]] = {}
        for row in req_rows:
            module_lessons_map.setdefault(row[1], []).append(row[0])

        for mod_id, lesson_ids in module_lessons_map.items():
            if all(lid in completed_ids for lid in lesson_ids):
                completed_modules += 1

        # 4. Upsert CourseProgress record
        now = datetime.now(timezone.utc)
        course_prog_stmt = select(CourseProgress).where(
            and_(
                CourseProgress.student_profile_id == student_profile_id,
                CourseProgress.course_offering_id == offering_id,
            )
        )
        cp_res = await db.execute(course_prog_stmt)
        course_prog = cp_res.scalar_one_or_none()

        if not course_prog:
            course_prog = CourseProgress(
                student_profile_id=student_profile_id,
                course_offering_id=offering_id,
                course_content_id=content_id,
                content_version=content_version,
                completed_lessons=completed_required_count,
                total_required_lessons=total_required_lessons,
                completed_modules=completed_modules,
                total_modules=total_modules,
                percentage=percentage,
                is_completed=is_completed,
                started_at=now,
                completed_at=now if is_completed else None,
                last_activity_at=now,
            )
            db.add(course_prog)
        else:
            course_prog.completed_lessons = completed_required_count
            course_prog.total_required_lessons = total_required_lessons
            course_prog.completed_modules = completed_modules
            course_prog.total_modules = total_modules
            course_prog.percentage = percentage
            course_prog.is_completed = is_completed
            if is_completed and not course_prog.completed_at:
                course_prog.completed_at = now
            course_prog.last_activity_at = now

        return course_prog

    @staticmethod
    async def get_course_progress(
        db: AsyncSession,
        user: User,
        course_offering_id: str,
    ) -> CourseProgress:
        profile = await ContentService.get_student_profile(db, user.id)
        stmt = select(CourseProgress).where(
            and_(
                CourseProgress.student_profile_id == profile.id,
                CourseProgress.course_offering_id == course_offering_id,
            )
        )
        res = await db.execute(stmt)
        progress = res.scalar_one_or_none()
        if not progress:
            # If not yet started, return 0 progress record
            _, offering, content = await ContentService.verify_student_course_enrollment(
                db, user, course_offering_id
            )
            progress = await ContentService._recalculate_course_progress(
                db, profile.id, offering.id, content.id, content.version
            )
            await db.commit()
            await db.refresh(progress)

        return progress

    # =====================================================================
    # 8. Bookmarks & Private Notes
    # =====================================================================

    @staticmethod
    async def create_bookmark(db: AsyncSession, user: User, data: BookmarkCreate) -> StudentBookmark:
        profile = await ContentService.get_student_profile(db, user.id)

        # Check existing
        existing_stmt = select(StudentBookmark).where(
            and_(
                StudentBookmark.student_profile_id == profile.id,
                StudentBookmark.target_type == data.target_type,
                StudentBookmark.target_id == data.target_id,
            )
        )
        existing_res = await db.execute(existing_stmt)
        if existing_res.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already bookmarked")

        bookmark = StudentBookmark(
            student_profile_id=profile.id,
            target_type=data.target_type,
            target_id=data.target_id,
            title=data.title,
            notes=data.notes,
        )
        db.add(bookmark)
        await db.commit()
        await db.refresh(bookmark)
        return bookmark

    @staticmethod
    async def list_bookmarks(db: AsyncSession, user: User) -> List[StudentBookmark]:
        profile = await ContentService.get_student_profile(db, user.id)
        stmt = (
            select(StudentBookmark)
            .where(StudentBookmark.student_profile_id == profile.id)
            .order_by(StudentBookmark.created_at.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def delete_bookmark(db: AsyncSession, user: User, bookmark_id: str) -> bool:
        profile = await ContentService.get_student_profile(db, user.id)
        stmt = select(StudentBookmark).where(
            and_(
                StudentBookmark.id == bookmark_id,
                StudentBookmark.student_profile_id == profile.id,
            )
        )
        res = await db.execute(stmt)
        bookmark = res.scalar_one_or_none()
        if not bookmark:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found")
        await db.delete(bookmark)
        await db.commit()
        return True

    @staticmethod
    async def create_learning_note(db: AsyncSession, user: User, data: LearningNoteCreate) -> StudentLearningNote:
        profile = await ContentService.get_student_profile(db, user.id)
        note = StudentLearningNote(
            student_profile_id=profile.id,
            target_type=data.target_type,
            target_id=data.target_id,
            title=data.title,
            content=data.content,
            is_private=data.is_private,
        )
        db.add(note)
        await db.commit()
        await db.refresh(note)
        return note

    @staticmethod
    async def list_learning_notes(
        db: AsyncSession,
        user: User,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
    ) -> List[StudentLearningNote]:
        profile = await ContentService.get_student_profile(db, user.id)
        conditions = [StudentLearningNote.student_profile_id == profile.id]
        if target_type:
            conditions.append(StudentLearningNote.target_type == target_type)
        if target_id:
            conditions.append(StudentLearningNote.target_id == target_id)

        stmt = select(StudentLearningNote).where(and_(*conditions)).order_by(StudentLearningNote.created_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def update_learning_note(
        db: AsyncSession,
        user: User,
        note_id: str,
        data: LearningNoteUpdate,
    ) -> StudentLearningNote:
        profile = await ContentService.get_student_profile(db, user.id)
        stmt = select(StudentLearningNote).where(
            and_(
                StudentLearningNote.id == note_id,
                StudentLearningNote.student_profile_id == profile.id,
            )
        )
        res = await db.execute(stmt)
        note = res.scalar_one_or_none()
        if not note:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning note not found")

        update_data = data.model_dump(exclude_unset=True)
        for key, val in update_data.items():
            setattr(note, key, val)

        await db.commit()
        await db.refresh(note)
        return note

    @staticmethod
    async def delete_learning_note(db: AsyncSession, user: User, note_id: str) -> bool:
        profile = await ContentService.get_student_profile(db, user.id)
        stmt = select(StudentLearningNote).where(
            and_(
                StudentLearningNote.id == note_id,
                StudentLearningNote.student_profile_id == profile.id,
            )
        )
        res = await db.execute(stmt)
        note = res.scalar_one_or_none()
        if not note:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning note not found")
        await db.delete(note)
        await db.commit()
        return True

    # =====================================================================
    # 9. Course Search & Discovery
    # =====================================================================

    @staticmethod
    async def search_courses(
        db: AsyncSession,
        user: User,
        query: Optional[str] = None,
        difficulty: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        # Enforce institution isolation for non-superadmins
        inst_id = user.institution_id if user.role != UserRole.SUPER_ADMIN else None

        stmt = select(Course).options(
            selectinload(Course.department),
            selectinload(Course.institution),
        )

        conditions = []
        if inst_id:
            conditions.append(Course.institution_id == inst_id)

        if query:
            search_pattern = f"%{query}%"
            conditions.append(
                or_(
                    Course.title.ilike(search_pattern),
                    Course.code.ilike(search_pattern),
                    Course.description.ilike(search_pattern),
                )
            )

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(Course.code.asc()).limit(limit).offset(offset)
        res = await db.execute(stmt)
        courses = res.scalars().all()

        results = []
        for c in courses:
            # Check content
            content_stmt = select(CourseContent).where(CourseContent.course_id == c.id)
            if user.role == UserRole.STUDENT:
                content_stmt = content_stmt.where(CourseContent.status == "published")
            if status_filter:
                content_stmt = content_stmt.where(CourseContent.status == status_filter)

            c_res = await db.execute(content_stmt)
            content = c_res.scalar_one_or_none()

            results.append({
                "course_id": c.id,
                "course_code": c.code,
                "course_title": c.title,
                "institution_id": c.institution_id,
                "course_content_id": content.id if content else None,
                "content_title": content.title if content else None,
                "short_description": content.short_description if content else c.description,
                "difficulty": content.difficulty if content else None,
                "status": content.status if content else "no_content",
            })

        return results
