"""Database models for Course Delivery, Curriculum Structure & Learning Content Engine (Domain 4).

Provides:
- CourseContent & CourseContentVersion
- Curriculum, Module, Lesson, LessonContentBlock
- LearningObjective
- Concept, ConceptPrerequisite, LessonConcept, ConceptSkill, LessonSkill, CourseSkill
- LearningResource, ResourceVersion, LessonResource
- ContentReview, ContentReviewComment
- Deterministic Student Learning Progress (LessonProgress, CourseProgress)
- StudentBookmark, StudentLearningNote
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    Integer,
    Float,
    ForeignKey,
    UniqueConstraint,
    Text,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


# =========================================================================
# 1. Course Content & Content Versioning
# =========================================================================

class CourseContent(Base):
    """Reusable, version-aware course learning content structure."""
    __tablename__ = "course_contents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=False)
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False)
    course_catalog_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("course_catalogs.id", ondelete="SET NULL"), index=True, nullable=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    detailed_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    learning_objectives: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    target_audience: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(50), default="intermediate", nullable=False)  # beginner, intermediate, advanced
    estimated_duration: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    language: Mapped[str] = mapped_column(String(50), default="English", nullable=False)

    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)  # draft, in_review, published, archived
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    author_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    owner_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    institution: Mapped["Institution"] = relationship("Institution")
    course: Mapped["Course"] = relationship("Course")
    course_catalog: Mapped[Optional["CourseCatalog"]] = relationship("CourseCatalog")
    author: Mapped[Optional["User"]] = relationship("User", foreign_keys=[author_id])
    owner: Mapped[Optional["User"]] = relationship("User", foreign_keys=[owner_id])

    curriculum: Mapped[Optional["Curriculum"]] = relationship("Curriculum", back_populates="course_content", uselist=False, cascade="all, delete-orphan", lazy="selectin")
    versions: Mapped[List["CourseContentVersion"]] = relationship("CourseContentVersion", back_populates="course_content", cascade="all, delete-orphan")
    reviews: Mapped[List["ContentReview"]] = relationship("ContentReview", back_populates="course_content", cascade="all, delete-orphan")
    skills: Mapped[List["CourseSkill"]] = relationship("CourseSkill", back_populates="course_content", cascade="all, delete-orphan")
    progress_records: Mapped[List["CourseProgress"]] = relationship("CourseProgress", back_populates="course_content", cascade="all, delete-orphan")


class CourseContentVersion(Base):
    """Immutable snapshot or publication record of course learning content."""
    __tablename__ = "course_content_versions"
    __table_args__ = (
        UniqueConstraint("course_content_id", "version_number", name="uq_course_content_version_num"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    course_content_id: Mapped[str] = mapped_column(String(36), ForeignKey("course_contents.id", ondelete="CASCADE"), index=True, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)  # draft, published, archived
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    change_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    snapshot_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    course_content: Mapped["CourseContent"] = relationship("CourseContent", back_populates="versions")
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])


# =========================================================================
# 2. Structured Curriculum, Modules, Lessons & Blocks
# =========================================================================

class Curriculum(Base):
    """Curriculum container belonging to CourseContent."""
    __tablename__ = "curriculums"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    course_content_id: Mapped[str] = mapped_column(String(36), ForeignKey("course_contents.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ordering_type: Mapped[str] = mapped_column(String(50), default="sequential", nullable=False)
    estimated_duration: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    learning_objectives: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    course_content: Mapped["CourseContent"] = relationship("CourseContent", back_populates="curriculum")
    modules: Mapped[List["Module"]] = relationship("Module", back_populates="curriculum", order_by="Module.order_index", cascade="all, delete-orphan", lazy="selectin")


class Module(Base):
    """Structured unit or chapter within a curriculum."""
    __tablename__ = "modules"
    __table_args__ = (
        UniqueConstraint("curriculum_id", "order_index", name="uq_module_curriculum_order"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    curriculum_id: Mapped[str] = mapped_column(String(36), ForeignKey("curriculums.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    learning_objectives: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    prerequisites: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # List of prerequisite module IDs
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    curriculum: Mapped["Curriculum"] = relationship("Curriculum", back_populates="modules")
    lessons: Mapped[List["Lesson"]] = relationship("Lesson", back_populates="module", order_by="Lesson.order_index", cascade="all, delete-orphan", lazy="selectin")


class Lesson(Base):
    """Individual learning unit containing structured content blocks."""
    __tablename__ = "lessons"
    __table_args__ = (
        UniqueConstraint("module_id", "order_index", name="uq_lesson_module_order"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    module_id: Mapped[str] = mapped_column(String(36), ForeignKey("modules.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lesson_type: Mapped[str] = mapped_column(String(50), default="text", nullable=False)  # text, video, article, interactive, coding, quiz, assignment, project, mixed
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_minutes: Mapped[Optional[int]] = mapped_column(Integer, default=15, nullable=True)
    learning_objectives: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    prerequisites: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # List of prerequisite lesson IDs
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    content_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    module: Mapped["Module"] = relationship("Module", back_populates="lessons")
    content_blocks: Mapped[List["LessonContentBlock"]] = relationship("LessonContentBlock", back_populates="lesson", order_by="LessonContentBlock.order_index", cascade="all, delete-orphan", lazy="selectin")
    concepts: Mapped[List["LessonConcept"]] = relationship("LessonConcept", back_populates="lesson", cascade="all, delete-orphan")
    skills: Mapped[List["LessonSkill"]] = relationship("LessonSkill", back_populates="lesson", cascade="all, delete-orphan")
    resources: Mapped[List["LessonResource"]] = relationship("LessonResource", back_populates="lesson", cascade="all, delete-orphan")
    learning_objectives_rel: Mapped[List["LearningObjective"]] = relationship("LearningObjective", back_populates="lesson", cascade="all, delete-orphan")
    progress_records: Mapped[List["LessonProgress"]] = relationship("LessonProgress", back_populates="lesson", cascade="all, delete-orphan")


class LessonContentBlock(Base):
    """Structured, typed content block composing a lesson."""
    __tablename__ = "lesson_content_blocks"
    __table_args__ = (
        UniqueConstraint("lesson_id", "order_index", name="uq_block_lesson_order"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lesson_id: Mapped[str] = mapped_column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), index=True, nullable=False)
    block_type: Mapped[str] = mapped_column(String(50), nullable=False)  # heading, paragraph, image, video, code, callout, quote, resource, embed
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # Sanitized text / markdown / HTML
    media_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    block_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="content_blocks")


class LearningObjective(Base):
    """Specific, measurable outcome attached to course content or a lesson."""
    __tablename__ = "learning_objectives"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    course_content_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("course_contents.id", ondelete="CASCADE"), index=True, nullable=True)
    lesson_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), index=True, nullable=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    measurable_outcome: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    taxonomy_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # remember, understand, apply, analyze, evaluate, create

    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    teacher_approved: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    lesson: Mapped[Optional["Lesson"]] = relationship("Lesson", back_populates="learning_objectives_rel")


# =========================================================================
# 3. Canonical Knowledge Units & Concept Graph
# =========================================================================

class Concept(Base):
    """Reusable canonical knowledge unit across courses."""
    __tablename__ = "concepts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    discipline_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("academic_disciplines.id", ondelete="SET NULL"), index=True, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(50), default="intermediate", nullable=False)  # beginner, intermediate, advanced
    parent_concept_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("concepts.id", ondelete="SET NULL"), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    discipline: Mapped[Optional["AcademicDiscipline"]] = relationship("AcademicDiscipline")
    parent_concept: Mapped[Optional["Concept"]] = relationship("Concept", remote_side=[id])

    prerequisites: Mapped[List["ConceptPrerequisite"]] = relationship(
        "ConceptPrerequisite",
        foreign_keys="[ConceptPrerequisite.concept_id]",
        back_populates="concept",
        cascade="all, delete-orphan",
    )
    prerequisite_for: Mapped[List["ConceptPrerequisite"]] = relationship(
        "ConceptPrerequisite",
        foreign_keys="[ConceptPrerequisite.prerequisite_concept_id]",
        back_populates="prerequisite_concept",
        cascade="all, delete-orphan",
    )
    skills: Mapped[List["ConceptSkill"]] = relationship("ConceptSkill", back_populates="concept", cascade="all, delete-orphan")
    lesson_mappings: Mapped[List["LessonConcept"]] = relationship("LessonConcept", back_populates="concept", cascade="all, delete-orphan")


class ConceptPrerequisite(Base):
    """Directed prerequisite relationship between canonical concepts."""
    __tablename__ = "concept_prerequisites"
    __table_args__ = (
        UniqueConstraint("concept_id", "prerequisite_concept_id", name="uq_concept_prerequisite"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    concept_id: Mapped[str] = mapped_column(String(36), ForeignKey("concepts.id", ondelete="CASCADE"), index=True, nullable=False)
    prerequisite_concept_id: Mapped[str] = mapped_column(String(36), ForeignKey("concepts.id", ondelete="CASCADE"), index=True, nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(50), default="prerequisite", nullable=False)  # prerequisite, related

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    concept: Mapped["Concept"] = relationship("Concept", foreign_keys=[concept_id], back_populates="prerequisites")
    prerequisite_concept: Mapped["Concept"] = relationship("Concept", foreign_keys=[prerequisite_concept_id], back_populates="prerequisite_for")


class LessonConcept(Base):
    """Mapping between a Lesson and a canonical Concept."""
    __tablename__ = "lesson_concepts"
    __table_args__ = (
        UniqueConstraint("lesson_id", "concept_id", name="uq_lesson_concept"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lesson_id: Mapped[str] = mapped_column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), index=True, nullable=False)
    concept_id: Mapped[str] = mapped_column(String(36), ForeignKey("concepts.id", ondelete="CASCADE"), index=True, nullable=False)
    importance: Mapped[str] = mapped_column(String(50), default="primary", nullable=False)  # primary, secondary, prerequisite

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="concepts")
    concept: Mapped["Concept"] = relationship("Concept", back_populates="lesson_mappings")


class ConceptSkill(Base):
    """Mapping between a Concept and a SkillCatalog skill."""
    __tablename__ = "concept_skills"
    __table_args__ = (
        UniqueConstraint("concept_id", "skill_id", name="uq_concept_skill"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    concept_id: Mapped[str] = mapped_column(String(36), ForeignKey("concepts.id", ondelete="CASCADE"), index=True, nullable=False)
    skill_id: Mapped[str] = mapped_column(String(36), ForeignKey("skill_catalogs.id", ondelete="CASCADE"), index=True, nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    expected_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # beginner, intermediate, advanced

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    concept: Mapped["Concept"] = relationship("Concept", back_populates="skills")
    skill: Mapped["SkillCatalog"] = relationship("SkillCatalog")


class LessonSkill(Base):
    """Mapping between a Lesson and a SkillCatalog skill."""
    __tablename__ = "lesson_skills"
    __table_args__ = (
        UniqueConstraint("lesson_id", "skill_id", name="uq_lesson_skill"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lesson_id: Mapped[str] = mapped_column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), index=True, nullable=False)
    skill_id: Mapped[str] = mapped_column(String(36), ForeignKey("skill_catalogs.id", ondelete="CASCADE"), index=True, nullable=False)
    importance: Mapped[str] = mapped_column(String(50), default="medium", nullable=False)  # primary, medium, secondary
    expected_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    evidence_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # completed_lesson, quiz, project

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="skills")
    skill: Mapped["SkillCatalog"] = relationship("SkillCatalog")


class CourseSkill(Base):
    """Mapping between a CourseContent and a SkillCatalog skill."""
    __tablename__ = "course_skills"
    __table_args__ = (
        UniqueConstraint("course_content_id", "skill_id", name="uq_course_skill"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    course_content_id: Mapped[str] = mapped_column(String(36), ForeignKey("course_contents.id", ondelete="CASCADE"), index=True, nullable=False)
    skill_id: Mapped[str] = mapped_column(String(36), ForeignKey("skill_catalogs.id", ondelete="CASCADE"), index=True, nullable=False)
    importance: Mapped[str] = mapped_column(String(50), default="primary", nullable=False)
    expected_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    course_content: Mapped["CourseContent"] = relationship("CourseContent", back_populates="skills")
    skill: Mapped["SkillCatalog"] = relationship("SkillCatalog")


# =========================================================================
# 4. Learning Resources & Resource Versioning
# =========================================================================

class LearningResource(Base):
    """Multimedia or document resource attached to courses or lessons."""
    __tablename__ = "learning_resources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)  # document, pdf, article, video, external_link, dataset, reference_book, code_repository, image
    storage_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    provider: Mapped[Optional[str]] = mapped_column(String(100), default="local", nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    access_level: Mapped[str] = mapped_column(String(50), default="course_only", nullable=False)  # public, institution_only, course_only, enrolled_students, faculty_only
    copyright_license: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    institution: Mapped[Optional["Institution"]] = relationship("Institution")
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])
    versions: Mapped[List["ResourceVersion"]] = relationship("ResourceVersion", back_populates="resource", cascade="all, delete-orphan")
    lesson_mappings: Mapped[List["LessonResource"]] = relationship("LessonResource", back_populates="resource", cascade="all, delete-orphan")


class ResourceVersion(Base):
    """Versioned file or URL record for a learning resource."""
    __tablename__ = "resource_versions"
    __table_args__ = (
        UniqueConstraint("resource_id", "version_number", name="uq_resource_version_num"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_id: Mapped[str] = mapped_column(String(36), ForeignKey("learning_resources.id", ondelete="CASCADE"), index=True, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    checksum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    uploaded_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    change_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    resource: Mapped["LearningResource"] = relationship("LearningResource", back_populates="versions")
    uploader: Mapped[Optional["User"]] = relationship("User", foreign_keys=[uploaded_by])


class LessonResource(Base):
    """Attachment relationship between a Lesson and a LearningResource."""
    __tablename__ = "lesson_resources"
    __table_args__ = (
        UniqueConstraint("lesson_id", "resource_id", name="uq_lesson_resource"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lesson_id: Mapped[str] = mapped_column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), index=True, nullable=False)
    resource_id: Mapped[str] = mapped_column(String(36), ForeignKey("learning_resources.id", ondelete="CASCADE"), index=True, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="resources")
    resource: Mapped["LearningResource"] = relationship("LearningResource", back_populates="lesson_mappings")


# =========================================================================
# 5. Course Content Review Workflow
# =========================================================================

class ContentReview(Base):
    """Formal peer or admin review record for course content transitions."""
    __tablename__ = "content_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    course_content_id: Mapped[str] = mapped_column(String(36), ForeignKey("course_contents.id", ondelete="CASCADE"), index=True, nullable=False)
    version_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("course_content_versions.id", ondelete="SET NULL"), index=True, nullable=True)
    submitted_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)

    status: Mapped[str] = mapped_column(String(30), default="submitted", nullable=False)  # submitted, approved, changes_requested, cancelled
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    course_content: Mapped["CourseContent"] = relationship("CourseContent", back_populates="reviews")
    submitter: Mapped["User"] = relationship("User", foreign_keys=[submitted_by])
    reviewer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reviewed_by])
    comments: Mapped[List["ContentReviewComment"]] = relationship("ContentReviewComment", back_populates="review", cascade="all, delete-orphan", lazy="selectin")


class ContentReviewComment(Base):
    """Detailed contextual feedback comments on a review."""
    __tablename__ = "content_review_comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    review_id: Mapped[str] = mapped_column(String(36), ForeignKey("content_reviews.id", ondelete="CASCADE"), index=True, nullable=False)
    author_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    module_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("modules.id", ondelete="SET NULL"), nullable=True)
    lesson_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True)
    comment: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    review: Mapped["ContentReview"] = relationship("ContentReview", back_populates="comments")
    author: Mapped["User"] = relationship("User", foreign_keys=[author_id])


# =========================================================================
# 6. Deterministic Student Learning Progress
# =========================================================================

class LessonProgress(Base):
    """Deterministic student progress for an individual lesson within a course offering."""
    __tablename__ = "lesson_progress"
    __table_args__ = (
        UniqueConstraint("student_profile_id", "lesson_id", "course_offering_id", name="uq_student_lesson_offering_progress"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    lesson_id: Mapped[str] = mapped_column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), index=True, nullable=False)
    course_offering_id: Mapped[str] = mapped_column(String(36), ForeignKey("course_offerings.id", ondelete="CASCADE"), index=True, nullable=False)
    content_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    status: Mapped[str] = mapped_column(String(30), default="not_started", nullable=False)  # not_started, in_progress, completed
    completion_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    student_profile: Mapped["StudentAcademicProfile"] = relationship("StudentAcademicProfile")
    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="progress_records")
    offering: Mapped["CourseOffering"] = relationship("CourseOffering")


class CourseProgress(Base):
    """Deterministic roll-up course progress for a student in a course offering."""
    __tablename__ = "course_progress"
    __table_args__ = (
        UniqueConstraint("student_profile_id", "course_offering_id", name="uq_student_course_offering_progress"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    course_offering_id: Mapped[str] = mapped_column(String(36), ForeignKey("course_offerings.id", ondelete="CASCADE"), index=True, nullable=False)
    course_content_id: Mapped[str] = mapped_column(String(36), ForeignKey("course_contents.id", ondelete="CASCADE"), index=True, nullable=False)
    content_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    completed_lessons: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_required_lessons: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_modules: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_modules: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    student_profile: Mapped["StudentAcademicProfile"] = relationship("StudentAcademicProfile")
    offering: Mapped["CourseOffering"] = relationship("CourseOffering")
    course_content: Mapped["CourseContent"] = relationship("CourseContent", back_populates="progress_records")


# =========================================================================
# 7. Student Bookmarks & Private Notes
# =========================================================================

class StudentBookmark(Base):
    """Personal bookmark saved by an authenticated student."""
    __tablename__ = "student_bookmarks"
    __table_args__ = (
        UniqueConstraint("student_profile_id", "target_type", "target_id", name="uq_student_bookmark"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)  # course, module, lesson, resource
    target_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    student_profile: Mapped["StudentAcademicProfile"] = relationship("StudentAcademicProfile")


class StudentLearningNote(Base):
    """Private student learning notes attached to a course, module, lesson, concept, or resource."""
    __tablename__ = "student_learning_notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)  # course, module, lesson, concept, resource
    target_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_private: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    student_profile: Mapped["StudentAcademicProfile"] = relationship("StudentAcademicProfile")
