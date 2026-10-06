"""Database models for Assessment Engine, Question Banks, Evaluation & Deterministic Evidence (Domain 5).

Provides:
- QuestionBank, EvaluationRubric, RubricCriterion
- Question, QuestionVersion, QuestionOption, QuestionConcept, QuestionSkill
- CodingConfiguration, CodingTestCase
- Assessment, AssessmentBlueprint, AssessmentVersion, AssessmentQuestion
- AssessmentAttempt, AssessmentResponse, AssessmentEvaluation, ManualEvaluation
- AssessmentResult, ConceptEvidence, SkillEvidence, GradeScheme
- AssessmentIntegrityEvent, AssessmentReview
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    Integer,
    Float,
    Numeric,
    ForeignKey,
    UniqueConstraint,
    Text,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


# =========================================================================
# 1. Question Bank & Rubrics
# =========================================================================

class QuestionBank(Base):
    """Institutional question bank container."""
    __tablename__ = "question_banks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=False)
    owner_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    department_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("departments.id", ondelete="SET NULL"), index=True, nullable=True)
    course_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("courses.id", ondelete="SET NULL"), index=True, nullable=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)  # draft, active, archived
    visibility: Mapped[str] = mapped_column(String(30), default="institution", nullable=False)  # institution, department, course, public

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    questions: Mapped[List["Question"]] = relationship("Question", back_populates="bank", cascade="all, delete-orphan", lazy="selectin")


class EvaluationRubric(Base):
    """Grading rubric for subjective and case-study questions."""
    __tablename__ = "evaluation_rubrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    criteria: Mapped[List["RubricCriterion"]] = relationship("RubricCriterion", back_populates="rubric", cascade="all, delete-orphan", lazy="selectin")


class RubricCriterion(Base):
    """Individual grading criteria within an evaluation rubric."""
    __tablename__ = "rubric_criteria"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rubric_id: Mapped[str] = mapped_column(String(36), ForeignKey("evaluation_rubrics.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    max_points: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("10.00"), nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("1.00"), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    rubric: Mapped["EvaluationRubric"] = relationship("EvaluationRubric", back_populates="criteria")


# =========================================================================
# 2. Question, Question Version & Metadata
# =========================================================================

class Question(Base):
    """Canonical question entity inside a question bank."""
    __tablename__ = "assessment_bank_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bank_id: Mapped[str] = mapped_column(String(36), ForeignKey("question_banks.id", ondelete="CASCADE"), index=True, nullable=False)
    question_type: Mapped[str] = mapped_column(String(50), nullable=False)  # single_choice, multiple_choice, true_false, fill_blank, short_answer, long_answer, coding, numeric, ordering, matching, case_study
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(30), default="medium", nullable=False)  # easy, medium, hard, expert
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)  # draft, in_review, approved, archived

    author_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    reviewer_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    bank: Mapped["QuestionBank"] = relationship("QuestionBank", back_populates="questions")
    versions: Mapped[List["QuestionVersion"]] = relationship("QuestionVersion", back_populates="question", cascade="all, delete-orphan", lazy="selectin")


class QuestionVersion(Base):
    """Immutable point-in-time snapshot of question prompt, scoring, and evaluation configuration."""
    __tablename__ = "question_versions"
    __table_args__ = (
        UniqueConstraint("question_id", "version_number", name="uq_question_version_num"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessment_bank_questions.id", ondelete="CASCADE"), index=True, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)

    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    points: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("1.00"), nullable=False)
    negative_marks: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    estimated_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(30), default="medium", nullable=False)

    rubric_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("evaluation_rubrics.id", ondelete="SET NULL"), index=True, nullable=True)
    evaluation_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    question: Mapped["Question"] = relationship("Question", back_populates="versions", lazy="selectin")
    options: Mapped[List["QuestionOption"]] = relationship("QuestionOption", back_populates="question_version", cascade="all, delete-orphan", lazy="selectin")
    concepts: Mapped[List["QuestionConcept"]] = relationship("QuestionConcept", back_populates="question_version", cascade="all, delete-orphan", lazy="selectin")
    skills: Mapped[List["QuestionSkill"]] = relationship("QuestionSkill", back_populates="question_version", cascade="all, delete-orphan", lazy="selectin")
    coding_config: Mapped[Optional["CodingConfiguration"]] = relationship("CodingConfiguration", back_populates="question_version", cascade="all, delete-orphan", uselist=False, lazy="selectin")
    rubric: Mapped[Optional["EvaluationRubric"]] = relationship("EvaluationRubric", lazy="selectin")


class QuestionOption(Base):
    """Options for objective questions (choice, true/false, ordering, matching)."""
    __tablename__ = "question_options"
    __table_args__ = (
        UniqueConstraint("question_version_id", "order_index", name="uq_question_option_order"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("question_versions.id", ondelete="CASCADE"), index=True, nullable=False)
    option_text: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    question_version: Mapped["QuestionVersion"] = relationship("QuestionVersion", back_populates="options")


class QuestionConcept(Base):
    """Mapping between a question version and canonical knowledge concepts."""
    __tablename__ = "question_concepts"
    __table_args__ = (
        UniqueConstraint("question_version_id", "concept_id", name="uq_question_concept"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("question_versions.id", ondelete="CASCADE"), index=True, nullable=False)
    concept_id: Mapped[str] = mapped_column(String(36), ForeignKey("concepts.id", ondelete="CASCADE"), index=True, nullable=False)
    importance: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("1.00"), nullable=False)

    question_version: Mapped["QuestionVersion"] = relationship("QuestionVersion", back_populates="concepts")


class QuestionSkill(Base):
    """Mapping between a question version and canonical skills from SkillCatalog."""
    __tablename__ = "question_skills"
    __table_args__ = (
        UniqueConstraint("question_version_id", "skill_id", name="uq_question_skill"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("question_versions.id", ondelete="CASCADE"), index=True, nullable=False)
    skill_id: Mapped[str] = mapped_column(String(36), ForeignKey("skill_catalogs.id", ondelete="CASCADE"), index=True, nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("1.00"), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(50), default="assessment", nullable=False)

    question_version: Mapped["QuestionVersion"] = relationship("QuestionVersion", back_populates="skills")


# =========================================================================
# 3. Coding Configuration & Sandboxing Metadata
# =========================================================================

class CodingConfiguration(Base):
    """Execution constraints and environment settings for coding questions."""
    __tablename__ = "coding_configurations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("question_versions.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    language: Mapped[str] = mapped_column(String(50), default="python", nullable=False)
    starter_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    function_signature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    time_limit_ms: Mapped[int] = mapped_column(Integer, default=2000, nullable=False)
    memory_limit_mb: Mapped[int] = mapped_column(Integer, default=256, nullable=False)
    constraints_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    input_format: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_format: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    question_version: Mapped["QuestionVersion"] = relationship("QuestionVersion", back_populates="coding_config")
    test_cases: Mapped[List["CodingTestCase"]] = relationship("CodingTestCase", back_populates="coding_config", cascade="all, delete-orphan", lazy="selectin")


class CodingTestCase(Base):
    """Public and hidden test cases for coding evaluation."""
    __tablename__ = "coding_test_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    coding_config_id: Mapped[str] = mapped_column(String(36), ForeignKey("coding_configurations.id", ondelete="CASCADE"), index=True, nullable=False)
    input_data: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output: Mapped[str] = mapped_column(Text, nullable=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    points_weight: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("1.00"), nullable=False)

    coding_config: Mapped["CodingConfiguration"] = relationship("CodingConfiguration", back_populates="test_cases")


# =========================================================================
# 4. Assessment, Blueprints, & Versioning
# =========================================================================

class Assessment(Base):
    """Assessment definition root entity."""
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=False)
    course_offering_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("course_offerings.id", ondelete="SET NULL"), index=True, nullable=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assessment_type: Mapped[str] = mapped_column(String(50), default="quiz", nullable=False)  # practice, quiz, assignment, diagnostic, internal, midterm, end_semester, mock_exam, placement_test, skill_assessment, custom
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)  # draft, scheduled, open, closed, graded, archived
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_marks: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    passing_marks: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    attempts_allowed: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    randomization_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"randomize_questions": bool, "randomize_options": bool, "seed": int}
    feedback_policy: Mapped[str] = mapped_column(String(50), default="after_submission", nullable=False)  # immediate_feedback, after_submission, after_release, never
    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    late_submission_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    versions: Mapped[List["AssessmentVersion"]] = relationship("AssessmentVersion", back_populates="assessment", cascade="all, delete-orphan", lazy="selectin")
    blueprints: Mapped[List["AssessmentBlueprint"]] = relationship("AssessmentBlueprint", back_populates="assessment", cascade="all, delete-orphan", lazy="selectin")


class AssessmentBlueprint(Base):
    """Specification for deterministic question selection across difficulty, concepts, and types."""
    __tablename__ = "assessment_blueprints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rules_config: Mapped[dict] = mapped_column(JSON, nullable=False)  # {"difficulty": {"easy": 40, "medium": 40, "hard": 20}, "concepts": {...}}
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="blueprints")


class AssessmentVersion(Base):
    """Frozen point-in-time version of an assessment, ensuring attempt immutability."""
    __tablename__ = "assessment_versions"
    __table_args__ = (
        UniqueConstraint("assessment_id", "version_number", name="uq_assessment_version_num"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), index=True, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_marks: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    passing_marks: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    feedback_policy: Mapped[str] = mapped_column(String(50), default="after_submission", nullable=False)
    rules_snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_frozen: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="versions")
    assessment_questions: Mapped[List["AssessmentQuestion"]] = relationship("AssessmentQuestion", back_populates="assessment_version", cascade="all, delete-orphan", lazy="selectin")
    attempts: Mapped[List["AssessmentAttempt"]] = relationship("AssessmentAttempt", back_populates="assessment_version", cascade="all, delete-orphan", lazy="selectin")


class AssessmentQuestion(Base):
    """Associative model binding a QuestionVersion to an AssessmentVersion with section and order."""
    __tablename__ = "assessment_version_questions"
    __table_args__ = (
        UniqueConstraint("assessment_version_id", "question_version_id", name="uq_assessment_version_question"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessment_versions.id", ondelete="CASCADE"), index=True, nullable=False)
    question_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("question_versions.id", ondelete="CASCADE"), index=True, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    section_name: Mapped[str] = mapped_column(String(100), default="Default", nullable=False)
    custom_points: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    custom_negative_marks: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    assessment_version: Mapped["AssessmentVersion"] = relationship("AssessmentVersion", back_populates="assessment_questions")
    question_version: Mapped["QuestionVersion"] = relationship("QuestionVersion", lazy="selectin")


# =========================================================================
# 5. Assessment Attempts, Responses, & Evaluation
# =========================================================================

class AssessmentAttempt(Base):
    """An individual student's timed attempt of an assessment version."""
    __tablename__ = "assessment_attempts"
    __table_args__ = (
        UniqueConstraint("assessment_version_id", "student_profile_id", "attempt_number", name="uq_attempt_version_student_num"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessment_versions.id", ondelete="CASCADE"), index=True, nullable=False)
    student_profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    status: Mapped[str] = mapped_column(String(30), default="not_started", nullable=False)  # not_started, in_progress, submitted, under_evaluation, evaluated, cancelled, expired
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    evaluated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    score: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    is_passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    result_status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)  # draft, internal, released, recalled
    attempt_token: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    assessment_version: Mapped["AssessmentVersion"] = relationship("AssessmentVersion", back_populates="attempts")
    responses: Mapped[List["AssessmentResponse"]] = relationship("AssessmentResponse", back_populates="attempt", cascade="all, delete-orphan", lazy="selectin")
    evaluations: Mapped[List["AssessmentEvaluation"]] = relationship("AssessmentEvaluation", back_populates="attempt", cascade="all, delete-orphan", lazy="selectin")
    result: Mapped[Optional["AssessmentResult"]] = relationship("AssessmentResult", back_populates="attempt", cascade="all, delete-orphan", uselist=False, lazy="selectin")


class AssessmentResponse(Base):
    """An individual question response submitted or autosaved during an attempt."""
    __tablename__ = "assessment_responses"
    __table_args__ = (
        UniqueConstraint("attempt_id", "question_version_id", name="uq_attempt_question_response"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    attempt_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), index=True, nullable=False)
    question_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("question_versions.id", ondelete="CASCADE"), index=True, nullable=False)

    response_type: Mapped[str] = mapped_column(String(50), nullable=False)
    response_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    answered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    attempt: Mapped["AssessmentAttempt"] = relationship("AssessmentAttempt", back_populates="responses")
    question_version: Mapped["QuestionVersion"] = relationship("QuestionVersion", lazy="selectin")


class AssessmentEvaluation(Base):
    """Evaluation record per question response."""
    __tablename__ = "assessment_evaluations"
    __table_args__ = (
        UniqueConstraint("attempt_id", "question_version_id", name="uq_attempt_question_eval"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    attempt_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), index=True, nullable=False)
    question_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("question_versions.id", ondelete="CASCADE"), index=True, nullable=False)

    awarded_marks: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    penalty_marks: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    max_marks: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    evaluation_type: Mapped[str] = mapped_column(String(50), default="deterministic", nullable=False)  # deterministic, manual, coding_sandbox, ai_proposed
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    evaluator_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    attempt: Mapped["AssessmentAttempt"] = relationship("AssessmentAttempt", back_populates="evaluations")
    manual_evaluations: Mapped[List["ManualEvaluation"]] = relationship("ManualEvaluation", back_populates="evaluation", cascade="all, delete-orphan", lazy="selectin")


class ManualEvaluation(Base):
    """Rubric-criterion-level manual score assigned by an authorized instructor."""
    __tablename__ = "manual_evaluations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evaluation_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessment_evaluations.id", ondelete="CASCADE"), index=True, nullable=False)
    rubric_criterion_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("rubric_criteria.id", ondelete="SET NULL"), index=True, nullable=True)
    awarded_points: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    evaluator_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    graded_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    graded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    evaluation: Mapped["AssessmentEvaluation"] = relationship("AssessmentEvaluation", back_populates="manual_evaluations")


# =========================================================================
# 6. Results, Evidence Provenance, & Grading Schemes
# =========================================================================

class AssessmentResult(Base):
    """Authoritative aggregated assessment result."""
    __tablename__ = "assessment_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    attempt_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    total_marks_obtained: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    maximum_marks: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    grade: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    is_passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)  # draft, internal, released, recalled

    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    released_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    released_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    attempt: Mapped["AssessmentAttempt"] = relationship("AssessmentAttempt", back_populates="result")


class ConceptEvidence(Base):
    """Immutable evidence record linking a student's question performance to a canonical Concept."""
    __tablename__ = "concept_evidences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    concept_id: Mapped[str] = mapped_column(String(36), ForeignKey("concepts.id", ondelete="CASCADE"), index=True, nullable=False)
    question_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("question_versions.id", ondelete="CASCADE"), index=True, nullable=False)
    assessment_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("assessments.id", ondelete="SET NULL"), index=True, nullable=True)
    attempt_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("assessment_attempts.id", ondelete="SET NULL"), index=True, nullable=True)

    score: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    max_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("1.0000"), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(50), default="assessment", nullable=False)
    evaluation_method: Mapped[str] = mapped_column(String(50), default="deterministic", nullable=False)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )


class SkillEvidence(Base):
    """Immutable evidence record linking a student's question performance to canonical SkillCatalog."""
    __tablename__ = "skill_evidences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    skill_id: Mapped[str] = mapped_column(String(36), ForeignKey("skill_catalogs.id", ondelete="CASCADE"), index=True, nullable=False)
    question_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("question_versions.id", ondelete="CASCADE"), index=True, nullable=False)
    assessment_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("assessments.id", ondelete="SET NULL"), index=True, nullable=True)
    attempt_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("assessment_attempts.id", ondelete="SET NULL"), index=True, nullable=True)

    score: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("1.00"), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(50), default="assessment", nullable=False)
    evaluation_method: Mapped[str] = mapped_column(String(50), default="deterministic", nullable=False)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )


class GradeScheme(Base):
    """Institution or course-specific deterministic grading scale."""
    __tablename__ = "grade_schemes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rules_payload: Mapped[list] = mapped_column(JSON, nullable=False)  # [{"grade": "A+", "min_percentage": 90.0, "max_percentage": 100.0}, ...]

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )


class AssessmentIntegrityEvent(Base):
    """Anti-tamper audit signals recorded during an attempt."""
    __tablename__ = "assessment_integrity_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    attempt_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # window_blur, fullscreen_exit, tab_switch, submission
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    metadata_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class AssessmentReview(Base):
    """Peer-review and administrative sign-off workflow for assessments."""
    __tablename__ = "assessment_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), index=True, nullable=False)
    submitted_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="submitted", nullable=False)  # submitted, approved, changes_requested
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
