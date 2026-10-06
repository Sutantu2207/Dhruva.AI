"""Pydantic schemas for Course Delivery, Curriculum Structure & Learning Content Engine."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# =========================================================================
# 1. Course Content & Versions
# =========================================================================

class CourseContentBase(BaseModel):
    title: str = Field(..., max_length=255)
    short_description: Optional[str] = Field(None, max_length=500)
    detailed_description: Optional[str] = None
    learning_objectives: Optional[List[str]] = None
    target_audience: Optional[str] = Field(None, max_length=255)
    difficulty: str = Field("intermediate", max_length=50)
    estimated_duration: Optional[str] = Field(None, max_length=100)
    language: str = Field("English", max_length=50)


class CourseContentCreate(CourseContentBase):
    course_id: str
    course_catalog_id: Optional[str] = None


class CourseContentUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    short_description: Optional[str] = Field(None, max_length=500)
    detailed_description: Optional[str] = None
    learning_objectives: Optional[List[str]] = None
    target_audience: Optional[str] = Field(None, max_length=255)
    difficulty: Optional[str] = Field(None, max_length=50)
    estimated_duration: Optional[str] = Field(None, max_length=100)
    language: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = None


class CourseContentVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    course_content_id: str
    version_number: int
    status: str
    created_by: Optional[str] = None
    published_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    change_summary: Optional[str] = None
    created_at: datetime


# =========================================================================
# 2. Content Blocks
# =========================================================================

class ContentBlockCreate(BaseModel):
    block_type: str = Field(..., max_length=50)  # heading, paragraph, image, video, code, callout, quote, resource, embed
    order_index: int = 0
    content: str
    media_url: Optional[str] = None
    block_metadata: Optional[Dict[str, Any]] = None


class ContentBlockUpdate(BaseModel):
    block_type: Optional[str] = None
    order_index: Optional[int] = None
    content: Optional[str] = None
    media_url: Optional[str] = None
    block_metadata: Optional[Dict[str, Any]] = None


class ContentBlockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    lesson_id: str
    block_type: str
    order_index: int
    content: str
    media_url: Optional[str] = None
    block_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


# =========================================================================
# 3. Learning Objectives
# =========================================================================

class LearningObjectiveCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    order_index: int = 0
    measurable_outcome: Optional[str] = None
    taxonomy_level: Optional[str] = None
    is_ai_generated: bool = False
    teacher_approved: bool = True
    lesson_id: Optional[str] = None
    course_content_id: Optional[str] = None


class LearningObjectiveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    course_content_id: Optional[str] = None
    lesson_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    order_index: int
    measurable_outcome: Optional[str] = None
    taxonomy_level: Optional[str] = None
    is_ai_generated: bool
    teacher_approved: bool
    created_at: datetime
    updated_at: datetime


# =========================================================================
# 4. Concepts & Concept Mappings
# =========================================================================

class ConceptCreate(BaseModel):
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=255)
    description: Optional[str] = None
    discipline_id: Optional[str] = None
    difficulty: str = Field("intermediate", max_length=50)
    parent_concept_id: Optional[str] = None


class ConceptUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    discipline_id: Optional[str] = None
    difficulty: Optional[str] = None
    parent_concept_id: Optional[str] = None
    status: Optional[str] = None


class ConceptPrerequisiteCreate(BaseModel):
    prerequisite_concept_id: str
    relationship_type: str = "prerequisite"


class ConceptSkillCreate(BaseModel):
    skill_id: str
    weight: float = 1.0
    expected_level: Optional[str] = None


class LessonConceptCreate(BaseModel):
    concept_id: str
    importance: str = "primary"


class LessonSkillCreate(BaseModel):
    skill_id: str
    importance: str = "medium"
    expected_level: Optional[str] = None
    evidence_type: Optional[str] = None


class CourseSkillCreate(BaseModel):
    skill_id: str
    importance: str = "primary"
    expected_level: Optional[str] = None


class ConceptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    description: Optional[str] = None
    discipline_id: Optional[str] = None
    difficulty: str
    parent_concept_id: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


# =========================================================================
# 5. Resources & Attachments
# =========================================================================

class ResourceCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    resource_type: str = Field(..., max_length=50)  # document, pdf, article, video, external_link, dataset, reference_book, code_repository, image
    url: Optional[str] = None
    provider: Optional[str] = "local"
    duration_seconds: Optional[int] = None
    access_level: str = "course_only"  # public, institution_only, course_only, enrolled_students, faculty_only
    copyright_license: Optional[str] = None


class ResourceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    duration_seconds: Optional[int] = None
    access_level: Optional[str] = None
    copyright_license: Optional[str] = None
    status: Optional[str] = None


class LessonResourceAttach(BaseModel):
    resource_id: str
    order_index: int = 0
    is_mandatory: bool = False


class ResourceVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    resource_id: str
    version_number: int
    storage_key: Optional[str] = None
    url: Optional[str] = None
    checksum: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    uploaded_by: Optional[str] = None
    uploaded_at: datetime
    change_summary: Optional[str] = None


class ResourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    resource_type: str
    storage_key: Optional[str] = None
    url: Optional[str] = None
    provider: Optional[str] = None
    duration_seconds: Optional[int] = None
    file_metadata: Optional[Dict[str, Any]] = None
    access_level: str
    copyright_license: Optional[str] = None
    status: str
    current_version: int
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# =========================================================================
# 6. Lessons, Modules & Curriculum
# =========================================================================

class LessonCreate(BaseModel):
    title: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=255)
    description: Optional[str] = None
    lesson_type: str = "text"
    order_index: int = 0
    estimated_minutes: Optional[int] = 15
    learning_objectives: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    status: str = "active"
    is_required: bool = True


class LessonUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    lesson_type: Optional[str] = None
    order_index: Optional[int] = None
    estimated_minutes: Optional[int] = None
    learning_objectives: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    status: Optional[str] = None
    is_required: Optional[bool] = None


class LessonReorderRequest(BaseModel):
    lesson_ids: List[str]


class LessonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    module_id: str
    title: str
    slug: str
    description: Optional[str] = None
    lesson_type: str
    order_index: int
    estimated_minutes: Optional[int] = None
    learning_objectives: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    status: str
    content_version: int
    is_required: bool
    created_at: datetime
    updated_at: datetime
    content_blocks: List[ContentBlockResponse] = []


class ModuleCreate(BaseModel):
    title: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=255)
    description: Optional[str] = None
    order_index: int = 0
    estimated_minutes: Optional[int] = None
    learning_objectives: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    status: str = "active"


class ModuleUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    order_index: Optional[int] = None
    estimated_minutes: Optional[int] = None
    learning_objectives: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    status: Optional[str] = None


class ModuleReorderRequest(BaseModel):
    module_ids: List[str]


class ModuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    curriculum_id: str
    title: str
    slug: str
    description: Optional[str] = None
    order_index: int
    estimated_minutes: Optional[int] = None
    learning_objectives: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    status: str
    created_at: datetime
    updated_at: datetime
    lessons: List[LessonResponse] = []


class CurriculumCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    ordering_type: str = "sequential"
    estimated_duration: Optional[str] = None
    learning_objectives: Optional[List[str]] = None


class CurriculumUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    ordering_type: Optional[str] = None
    estimated_duration: Optional[str] = None
    learning_objectives: Optional[List[str]] = None
    status: Optional[str] = None


class CurriculumResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    course_content_id: str
    title: str
    description: Optional[str] = None
    ordering_type: str
    estimated_duration: Optional[str] = None
    learning_objectives: Optional[List[str]] = None
    status: str
    created_at: datetime
    updated_at: datetime
    modules: List[ModuleResponse] = []


class CourseContentDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    course_id: str
    course_catalog_id: Optional[str] = None
    title: str
    short_description: Optional[str] = None
    detailed_description: Optional[str] = None
    learning_objectives: Optional[List[str]] = None
    target_audience: Optional[str] = None
    difficulty: str
    estimated_duration: Optional[str] = None
    language: str
    status: str
    version: int
    author_id: Optional[str] = None
    owner_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    curriculum: Optional[CurriculumResponse] = None


# =========================================================================
# 7. Content Review Workflow
# =========================================================================

class ContentReviewSubmitRequest(BaseModel):
    review_notes: Optional[str] = None


class ContentReviewDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(approve|request_changes)$")
    review_notes: Optional[str] = None


class ContentReviewCommentCreate(BaseModel):
    comment: str
    module_id: Optional[str] = None
    lesson_id: Optional[str] = None


class ContentReviewCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    review_id: str
    author_id: str
    module_id: Optional[str] = None
    lesson_id: Optional[str] = None
    comment: str
    created_at: datetime


class ContentReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    course_content_id: str
    version_id: Optional[str] = None
    submitted_by: str
    reviewed_by: Optional[str] = None
    status: str
    review_notes: Optional[str] = None
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    comments: List[ContentReviewCommentResponse] = []


# =========================================================================
# 8. Deterministic Student Learning Progress
# =========================================================================

class LessonProgressStartRequest(BaseModel):
    course_offering_id: str


class LessonProgressUpdateRequest(BaseModel):
    course_offering_id: str
    time_spent_seconds: int = Field(default=0, ge=0)
    completion_percentage: float = Field(default=0.0, ge=0.0, le=100.0)


class LessonProgressCompleteRequest(BaseModel):
    course_offering_id: str
    time_spent_seconds: Optional[int] = Field(default=0, ge=0)


class LessonProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_profile_id: str
    lesson_id: str
    course_offering_id: str
    content_version: int
    status: str
    completion_percentage: float
    time_spent_seconds: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_accessed_at: datetime


class CourseProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_profile_id: str
    course_offering_id: str
    course_content_id: str
    content_version: int
    completed_lessons: int
    total_required_lessons: int
    completed_modules: int
    total_modules: int
    percentage: float
    is_completed: bool
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_activity_at: datetime


# =========================================================================
# 9. Bookmarks & Private Notes
# =========================================================================

class BookmarkCreate(BaseModel):
    target_type: str = Field(..., max_length=50)  # course, module, lesson, resource
    target_id: str = Field(..., max_length=36)
    title: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class BookmarkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_profile_id: str
    target_type: str
    target_id: str
    title: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime


class LearningNoteCreate(BaseModel):
    target_type: str = Field(..., max_length=50)  # course, module, lesson, concept, resource
    target_id: str = Field(..., max_length=36)
    title: Optional[str] = Field(None, max_length=255)
    content: str
    is_private: bool = True


class LearningNoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_private: Optional[bool] = None


class LearningNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_profile_id: str
    target_type: str
    target_id: str
    title: Optional[str] = None
    content: str
    is_private: bool
    created_at: datetime
    updated_at: datetime


# =========================================================================
# 10. Search & Catalog Discovery
# =========================================================================

class CourseSearchItem(BaseModel):
    course_id: str
    course_code: str
    course_title: str
    institution_id: str
    course_content_id: Optional[str] = None
    content_title: Optional[str] = None
    short_description: Optional[str] = None
    difficulty: Optional[str] = None
    status: Optional[str] = None
    modules_count: int = 0
    lessons_count: int = 0
