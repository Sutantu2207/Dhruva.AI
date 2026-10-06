"""REST API endpoints for Course Delivery, Curriculum Structure & Learning Content Engine (Domain 4).

Provides routers for:
- /courses: Course content containers, curriculum overview, course-level authoring & discovery
- /curriculum: Detailed curriculum structures
- /modules: Curriculum modules, ordering, and details
- /lessons: Lesson authoring, content blocks, resources, and concept mappings
- /concepts: Canonical knowledge graph, prerequisites, and skill mappings
- /resources: Learning resources, metadata, and uploads
- /learning: Deterministic lesson and course progress tracking
- /bookmarks: Student personal bookmarks
- /notes: Student private learning notes
- /content-review: Review submission, decisions, and feedback comments
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.api.deps import get_db, get_current_user, require_roles
from app.core.security import UserRole
from app.domains.identity.models import User
from app.domains.content.models import (
    CourseContent,
    Curriculum,
    Module,
    Lesson,
    LessonContentBlock,
    Concept,
    LearningResource,
    StudentBookmark,
    StudentLearningNote,
)
from app.domains.content.schemas import (
    CourseContentCreate,
    CourseContentUpdate,
    CourseContentDetailResponse,
    CurriculumCreate,
    CurriculumUpdate,
    CurriculumResponse,
    ModuleCreate,
    ModuleUpdate,
    ModuleReorderRequest,
    ModuleResponse,
    LessonCreate,
    LessonUpdate,
    LessonReorderRequest,
    LessonResponse,
    ContentBlockCreate,
    ContentBlockResponse,
    ConceptCreate,
    ConceptUpdate,
    ConceptResponse,
    ConceptPrerequisiteCreate,
    ConceptSkillCreate,
    LessonConceptCreate,
    LessonSkillCreate,
    CourseSkillCreate,
    ResourceCreate,
    ResourceResponse,
    LessonResourceAttach,
    ContentReviewSubmitRequest,
    ContentReviewDecisionRequest,
    ContentReviewCommentCreate,
    ContentReviewResponse,
    LessonProgressStartRequest,
    LessonProgressUpdateRequest,
    LessonProgressCompleteRequest,
    LessonProgressResponse,
    CourseProgressResponse,
    BookmarkCreate,
    BookmarkResponse,
    LearningNoteCreate,
    LearningNoteUpdate,
    LearningNoteResponse,
    CourseSearchItem,
)
from app.domains.content.service import ContentService

# Separate routers matching Section 36
courses_router = APIRouter(prefix="/courses", tags=["Course Content & Delivery"])
curriculum_router = APIRouter(prefix="/curriculum", tags=["Curriculum"])
modules_router = APIRouter(prefix="/modules", tags=["Modules"])
lessons_router = APIRouter(prefix="/lessons", tags=["Lessons"])
concepts_router = APIRouter(prefix="/concepts", tags=["Concepts & Knowledge Graph"])
resources_router = APIRouter(prefix="/resources", tags=["Learning Resources"])
learning_router = APIRouter(prefix="/learning", tags=["Learning Delivery & Progress"])
bookmarks_router = APIRouter(prefix="/bookmarks", tags=["Bookmarks"])
notes_router = APIRouter(prefix="/notes", tags=["Learning Notes"])
review_router = APIRouter(prefix="/content-review", tags=["Content Review"])


# =========================================================================
# 1. Courses Router (/courses)
# =========================================================================

@courses_router.get("", response_model=List[CourseSearchItem])
async def search_and_list_courses(
    q: Optional[str] = Query(None, description="Search course title, code, description"),
    difficulty: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search and discover courses scoped to the user's institution and authorization."""
    return await ContentService.search_courses(
        db=db,
        user=current_user,
        query=q,
        difficulty=difficulty,
        status_filter=status,
        limit=limit,
        offset=offset,
    )


@courses_router.get("/{id}", response_model=CourseContentDetailResponse)
async def get_course_content_details(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed course content container with curriculum tree."""
    return await ContentService.get_course_content_by_id(db=db, content_id=id, user=current_user)


@courses_router.get("/{id}/curriculum", response_model=CurriculumResponse)
async def get_course_curriculum(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the structured curriculum tree for a course (students only see published)."""
    return await ContentService.get_curriculum(db=db, course_id=id, user=current_user)


@courses_router.post(
    "/{id}/content",
    response_model=CourseContentDetailResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN))],
)
async def create_course_content_for_course(
    id: str,
    data: CourseContentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create learning content structure for a course (authorized faculty/admin)."""
    data.course_id = id
    content = await ContentService.create_course_content(db=db, user=current_user, data=data)
    return await ContentService.get_course_content_by_id(db=db, content_id=content.id, user=current_user)


@courses_router.patch(
    "/{id}/content",
    response_model=CourseContentDetailResponse,
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN))],
)
async def update_course_content(
    id: str,
    data: CourseContentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update course content metadata (draft/review only; published content is immutable)."""
    content = await ContentService.update_course_content(db=db, content_id=id, user=current_user, data=data)
    return await ContentService.get_course_content_by_id(db=db, content_id=content.id, user=current_user)


@courses_router.get("/{id}/modules", response_model=List[ModuleResponse])
async def list_course_modules(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List ordered modules for a course curriculum."""
    curriculum = await ContentService.get_curriculum(db=db, course_id=id, user=current_user)
    return curriculum.modules


@courses_router.post(
    "/{id}/modules",
    response_model=ModuleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN))],
)
async def create_course_module(
    id: str,
    data: ModuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a module to the course curriculum."""
    curriculum = await ContentService.get_curriculum(db=db, course_id=id, user=current_user)
    return await ContentService.create_module(db=db, curriculum_id=curriculum.id, user=current_user, data=data)


@courses_router.post(
    "/{id}/skills",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN))],
)
async def map_skill_to_course(
    id: str,
    data: CourseSkillCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Map a course content container to a SkillCatalog skill."""
    return await ContentService.map_course_skill(db=db, course_content_id=id, user=current_user, data=data)


# =========================================================================
# 2. Modules Router (/modules)
# =========================================================================

@modules_router.get("/{id}/lessons", response_model=List[LessonResponse])
async def list_module_lessons(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List ordered lessons in a module."""
    stmt = select(Lesson).where(Lesson.module_id == id).order_by(Lesson.order_index.asc())
    res = await db.execute(stmt)
    return list(res.scalars().all())


@modules_router.post(
    "/{id}/lessons",
    response_model=LessonResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN))],
)
async def create_module_lesson(
    id: str,
    data: LessonCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new lesson within a module."""
    return await ContentService.create_lesson(db=db, module_id=id, user=current_user, data=data)


@modules_router.patch(
    "/{id}",
    response_model=ModuleResponse,
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN))],
)
async def update_module(
    id: str,
    data: ModuleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update module title, description, or status."""
    stmt = select(Module).where(Module.id == id)
    res = await db.execute(stmt)
    module = res.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")

    update_dict = data.model_dump(exclude_unset=True)
    for key, val in update_dict.items():
        setattr(module, key, val)

    await db.commit()
    await db.refresh(module)
    return module


@modules_router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN))],
)
async def delete_module(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a module and its contents."""
    stmt = select(Module).where(Module.id == id)
    res = await db.execute(stmt)
    module = res.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    await db.delete(module)
    await db.commit()


@modules_router.post(
    "/reorder",
    response_model=List[ModuleResponse],
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN))],
)
async def reorder_curriculum_modules(
    curriculum_id: str = Query(...),
    request: ModuleReorderRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deterministically persist new ordering of modules."""
    return await ContentService.reorder_modules(
        db=db,
        curriculum_id=curriculum_id,
        user=current_user,
        module_ids=request.module_ids,
    )


# =========================================================================
# 3. Lessons Router (/lessons)
# =========================================================================

@lessons_router.get("/{id}", response_model=LessonResponse)
async def get_lesson_details(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve lesson details with structured content blocks."""
    stmt = select(Lesson).where(Lesson.id == id).options(selectinload(Lesson.content_blocks))
    res = await db.execute(stmt)
    lesson = res.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    return lesson


@lessons_router.patch(
    "/{id}",
    response_model=LessonResponse,
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN))],
)
async def update_lesson(
    id: str,
    data: LessonUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update lesson metadata or configuration."""
    stmt = select(Lesson).where(Lesson.id == id).options(selectinload(Lesson.content_blocks))
    res = await db.execute(stmt)
    lesson = res.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    update_dict = data.model_dump(exclude_unset=True)
    for key, val in update_dict.items():
        setattr(lesson, key, val)

    await db.commit()
    await db.refresh(lesson)
    return lesson


@lessons_router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN))],
)
async def delete_lesson(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a lesson and associated content blocks."""
    stmt = select(Lesson).where(Lesson.id == id)
    res = await db.execute(stmt)
    lesson = res.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    await db.delete(lesson)
    await db.commit()


@lessons_router.post(
    "/{id}/blocks",
    response_model=ContentBlockResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN))],
)
async def add_lesson_content_block(
    id: str,
    data: ContentBlockCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a sanitized, structured content block to a lesson."""
    return await ContentService.add_content_block(db=db, lesson_id=id, user=current_user, data=data)


@lessons_router.post(
    "/{id}/resources",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN))],
)
async def attach_resource_to_lesson(
    id: str,
    data: LessonResourceAttach,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Attach a learning resource to a lesson."""
    return await ContentService.attach_resource_to_lesson(db=db, lesson_id=id, user=current_user, data=data)


@lessons_router.post(
    "/{id}/concepts",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN))],
)
async def map_concept_to_lesson(
    id: str,
    data: LessonConceptCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Map a canonical concept to a lesson."""
    return await ContentService.map_lesson_concept(db=db, lesson_id=id, user=current_user, data=data)


@lessons_router.post(
    "/{id}/skills",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN))],
)
async def map_skill_to_lesson(
    id: str,
    data: LessonSkillCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Map a skill from Domain 2.5 SkillCatalog to a lesson."""
    return await ContentService.map_lesson_skill(db=db, lesson_id=id, user=current_user, data=data)


@lessons_router.post(
    "/reorder",
    response_model=List[LessonResponse],
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN))],
)
async def reorder_module_lessons(
    module_id: str = Query(...),
    request: LessonReorderRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deterministically persist new ordering of lessons within a module."""
    return await ContentService.reorder_lessons(
        db=db,
        module_id=module_id,
        user=current_user,
        lesson_ids=request.lesson_ids,
    )


# =========================================================================
# 4. Concepts Router (/concepts)
# =========================================================================

@concepts_router.get("", response_model=List[ConceptResponse])
async def list_concepts(
    q: Optional[str] = Query(None),
    discipline_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List canonical reusable concepts across courses."""
    stmt = select(Concept)
    if q:
        stmt = stmt.where(Concept.name.ilike(f"%{q}%"))
    if discipline_id:
        stmt = stmt.where(Concept.discipline_id == discipline_id)
    stmt = stmt.order_by(Concept.name.asc()).limit(limit).offset(offset)
    res = await db.execute(stmt)
    return list(res.scalars().all())


@concepts_router.post(
    "",
    response_model=ConceptResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN))],
)
async def create_concept(
    data: ConceptCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a canonical knowledge concept."""
    return await ContentService.create_concept(db=db, user=current_user, data=data)


@concepts_router.post(
    "/{id}/prerequisites",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN))],
)
async def add_concept_prerequisite(
    id: str,
    data: ConceptPrerequisiteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Declare a prerequisite concept relationship."""
    return await ContentService.add_concept_prerequisite(db=db, concept_id=id, user=current_user, data=data)


@concepts_router.post(
    "/{id}/skills",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN))],
)
async def map_skill_to_concept(
    id: str,
    data: ConceptSkillCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Map a canonical concept to a SkillCatalog skill."""
    return await ContentService.map_concept_skill(db=db, concept_id=id, user=current_user, data=data)


# =========================================================================
# 5. Resources Router (/resources)
# =========================================================================

@resources_router.post(
    "",
    response_model=ResourceResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN))],
)
async def create_learning_resource(
    data: ResourceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register a new learning resource."""
    return await ContentService.create_resource(db=db, user=current_user, data=data)


@resources_router.get("/{id}", response_model=ResourceResponse)
async def get_learning_resource(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get metadata for a learning resource."""
    stmt = select(LearningResource).where(LearningResource.id == id)
    res = await db.execute(stmt)
    resource = res.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return resource


# =========================================================================
# 6. Learning Delivery & Deterministic Progress Router (/learning)
# =========================================================================

@learning_router.post(
    "/lessons/{id}/start",
    response_model=LessonProgressResponse,
    dependencies=[Depends(require_roles(UserRole.STUDENT))],
)
async def start_lesson_progress(
    id: str,
    request: LessonProgressStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a lesson as started for the enrolled student."""
    return await ContentService.start_lesson(
        db=db,
        user=current_user,
        lesson_id=id,
        course_offering_id=request.course_offering_id,
    )


@learning_router.post(
    "/lessons/{id}/progress",
    response_model=LessonProgressResponse,
    dependencies=[Depends(require_roles(UserRole.STUDENT))],
)
async def update_lesson_progress(
    id: str,
    request: LessonProgressUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update active reading or playback progress for a lesson."""
    return await ContentService.update_lesson_progress(
        db=db,
        user=current_user,
        lesson_id=id,
        data=request,
    )


@learning_router.post(
    "/lessons/{id}/complete",
    response_model=LessonProgressResponse,
    dependencies=[Depends(require_roles(UserRole.STUDENT))],
)
async def complete_lesson_progress(
    id: str,
    request: LessonProgressCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a lesson completed and deterministically recalculate course progress."""
    lesson_prog, _ = await ContentService.complete_lesson(
        db=db,
        user=current_user,
        lesson_id=id,
        course_offering_id=request.course_offering_id,
        time_spent_seconds=request.time_spent_seconds or 0,
    )
    return lesson_prog


@learning_router.get(
    "/courses/{id}/progress",
    response_model=CourseProgressResponse,
    dependencies=[Depends(require_roles(UserRole.STUDENT))],
)
async def get_course_offering_progress(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get deterministic roll-up progress for an enrolled course offering."""
    return await ContentService.get_course_progress(
        db=db,
        user=current_user,
        course_offering_id=id,
    )


# =========================================================================
# 7. Bookmarks Router (/bookmarks)
# =========================================================================

@bookmarks_router.post(
    "",
    response_model=BookmarkResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.STUDENT))],
)
async def create_student_bookmark(
    data: BookmarkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save a private learning bookmark for the authenticated student."""
    return await ContentService.create_bookmark(db=db, user=current_user, data=data)


@bookmarks_router.get(
    "",
    response_model=List[BookmarkResponse],
    dependencies=[Depends(require_roles(UserRole.STUDENT))],
)
async def list_student_bookmarks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List private bookmarks for the authenticated student."""
    return await ContentService.list_bookmarks(db=db, user=current_user)


@bookmarks_router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(UserRole.STUDENT))],
)
async def delete_student_bookmark(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a student bookmark."""
    await ContentService.delete_bookmark(db=db, user=current_user, bookmark_id=id)


# =========================================================================
# 8. Learning Notes Router (/notes)
# =========================================================================

@notes_router.get(
    "",
    response_model=List[LearningNoteResponse],
    dependencies=[Depends(require_roles(UserRole.STUDENT))],
)
async def list_student_notes(
    target_type: Optional[str] = Query(None),
    target_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List private student learning notes."""
    return await ContentService.list_learning_notes(
        db=db,
        user=current_user,
        target_type=target_type,
        target_id=target_id,
    )


@notes_router.post(
    "",
    response_model=LearningNoteResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.STUDENT))],
)
async def create_student_note(
    data: LearningNoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a private learning note."""
    return await ContentService.create_learning_note(db=db, user=current_user, data=data)


@notes_router.patch(
    "/{id}",
    response_model=LearningNoteResponse,
    dependencies=[Depends(require_roles(UserRole.STUDENT))],
)
async def update_student_note(
    id: str,
    data: LearningNoteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a private learning note."""
    return await ContentService.update_learning_note(db=db, user=current_user, note_id=id, data=data)


@notes_router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(UserRole.STUDENT))],
)
async def delete_student_note(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a private learning note."""
    await ContentService.delete_learning_note(db=db, user=current_user, note_id=id)


# =========================================================================
# 9. Content Review Router (/content-review)
# =========================================================================

@review_router.post(
    "/{content_id}/submit",
    response_model=ContentReviewResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN))],
)
async def submit_content_for_review(
    content_id: str,
    request: ContentReviewSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a draft course content container for administrative review."""
    return await ContentService.submit_content_for_review(
        db=db,
        content_id=content_id,
        user=current_user,
        data=request,
    )


@review_router.post(
    "/{review_id}/approve",
    response_model=ContentReviewResponse,
    dependencies=[Depends(require_roles(UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN))],
)
async def approve_content_review(
    review_id: str,
    request: Optional[ContentReviewSubmitRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve content review and publish course content with an immutable snapshot version."""
    decision_data = ContentReviewDecisionRequest(
        decision="approve",
        review_notes=request.review_notes if request else "Approved for publication",
    )
    return await ContentService.decide_content_review(
        db=db,
        review_id=review_id,
        user=current_user,
        data=decision_data,
    )


@review_router.post(
    "/{review_id}/request-changes",
    response_model=ContentReviewResponse,
    dependencies=[Depends(require_roles(UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN))],
)
async def request_changes_content_review(
    review_id: str,
    request: ContentReviewSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Request changes on content review and return to draft status."""
    decision_data = ContentReviewDecisionRequest(
        decision="request_changes",
        review_notes=request.review_notes,
    )
    return await ContentService.decide_content_review(
        db=db,
        review_id=review_id,
        user=current_user,
        data=decision_data,
    )
