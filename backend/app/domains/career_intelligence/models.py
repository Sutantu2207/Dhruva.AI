"""Database models for Domain 7: Skill Intelligence, Career Trajectories & Placement Readiness."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    Integer,
    Text,
    JSON,
    UniqueConstraint,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class StudentSkillIntelligenceState(Base):
    """Authoritative evaluated skill intelligence state for a student, derived from multi-source evidence."""
    __tablename__ = "student_skill_intelligence_states"
    __table_args__ = (
        UniqueConstraint("student_profile_id", "skill_id", name="uq_student_skill_intelligence"),
        CheckConstraint("observed_proficiency >= 0.0 AND observed_proficiency <= 1.0", name="chk_skill_observed_range"),
        CheckConstraint("verified_proficiency >= 0.0 AND verified_proficiency <= 1.0", name="chk_skill_verified_range"),
        CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="chk_skill_confidence_range"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    skill_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("skill_catalogs.id", ondelete="CASCADE"), index=True, nullable=False
    )

    observed_proficiency: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    self_reported_proficiency: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    verified_proficiency: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)

    evidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    verified_evidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    assessment_evidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    project_evidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    course_evidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    certification_evidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    concept_mastery_contribution: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)

    verification_status: Mapped[str] = mapped_column(
        String(32), default="unverified", nullable=False, index=True
    )  # unverified, partially_verified, verified, certified
    proficiency_tier: Mapped[str] = mapped_column(
        String(32), default="exposure", nullable=False, index=True
    )  # exposure, beginner, developing, proficient, advanced

    algorithm_version: Mapped[str] = mapped_column(String(20), default="v1", nullable=False)
    last_evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    student_profile: Mapped["StudentAcademicProfile"] = relationship("StudentAcademicProfile")  # noqa: F821
    skill: Mapped["SkillCatalog"] = relationship("SkillCatalog")  # noqa: F821


class StudentSkillEvidenceRecord(Base):
    """Immutable provenance record tracking each piece of evidence incorporated into a student's skill state."""
    __tablename__ = "student_skill_evidence_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    skill_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("skill_catalogs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # assessment, coding_assessment, concept_mastery, project, course_completion, certification, faculty_verification, self_report
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    evidence_weight: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("1.0000"), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    provenance_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False
    )

    student_profile: Mapped["StudentAcademicProfile"] = relationship("StudentAcademicProfile")  # noqa: F821
    skill: Mapped["SkillCatalog"] = relationship("SkillCatalog")  # noqa: F821


class StudentCareerReadinessState(Base):
    """Authoritative evaluated career readiness and fit for a student towards a canonical CareerCatalog role."""
    __tablename__ = "student_career_readiness_states"
    __table_args__ = (
        UniqueConstraint("student_profile_id", "career_id", name="uq_student_career_readiness"),
        CheckConstraint("readiness_score >= 0.0 AND readiness_score <= 1.0", name="chk_career_readiness_range"),
        CheckConstraint("fit_score >= 0.0 AND fit_score <= 1.0", name="chk_career_fit_range"),
        CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="chk_career_confidence_range"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    career_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("career_catalogs.id", ondelete="CASCADE"), index=True, nullable=False
    )

    readiness_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False, index=True)
    fit_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)

    required_skill_coverage: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    preferred_skill_coverage: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    critical_skill_coverage: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)

    critical_gaps_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    strengths_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    developing_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    has_sufficient_catalog_data: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    status: Mapped[str] = mapped_column(
        String(32), default="assessed", nullable=False
    )  # assessed, insufficient_catalog_data, insufficient_student_evidence
    explanation_breakdown: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    algorithm_version: Mapped[str] = mapped_column(String(20), default="v1", nullable=False)
    last_evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    student_profile: Mapped["StudentAcademicProfile"] = relationship("StudentAcademicProfile")  # noqa: F821
    career: Mapped["CareerCatalog"] = relationship("CareerCatalog")  # noqa: F821


class CareerTrajectory(Base):
    """Persisted adaptive trajectory guiding a student toward a target career destination."""
    __tablename__ = "career_trajectories"
    __table_args__ = (
        UniqueConstraint("student_profile_id", "career_id", name="uq_student_career_trajectory"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    career_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("career_catalogs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default="in_progress", nullable=False
    )  # not_started, in_progress, completed, blocked
    total_steps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_steps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(20), default="v1", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    student_profile: Mapped["StudentAcademicProfile"] = relationship("StudentAcademicProfile")  # noqa: F821
    career: Mapped["CareerCatalog"] = relationship("CareerCatalog")  # noqa: F821
    steps: Mapped[List["CareerTrajectoryStep"]] = relationship(
        "CareerTrajectoryStep", back_populates="trajectory", cascade="all, delete-orphan", order_by="CareerTrajectoryStep.step_number"
    )


class CareerTrajectoryStep(Base):
    """Concrete milestone step connecting a skill gap to actionable curriculum or assessment resources."""
    __tablename__ = "career_trajectory_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trajectory_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("career_trajectories.id", ondelete="CASCADE"), index=True, nullable=False
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    skill_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("skill_catalogs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    step_type: Mapped[str] = mapped_column(
        String(50), default="concept_mastery", nullable=False
    )  # concept_mastery, lesson, course, practice, project, assessment, certification
    priority: Mapped[str] = mapped_column(
        String(32), default="medium", nullable=False
    )  # critical, high, medium, low
    status: Mapped[str] = mapped_column(
        String(32), default="not_started", nullable=False
    )  # not_started, in_progress, completed, blocked, not_available

    target_proficiency: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.7000"), nullable=False)
    current_proficiency: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    gap_size: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)

    reference_course_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("course_catalogs.id", ondelete="SET NULL"), nullable=True
    )
    reference_lesson_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True
    )
    reference_concept_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True
    )
    reference_assessment_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("assessments.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    trajectory: Mapped["CareerTrajectory"] = relationship("CareerTrajectory", back_populates="steps")
    skill: Mapped["SkillCatalog"] = relationship("SkillCatalog")  # noqa: F821


class PlacementReadinessState(Base):
    """Multi-component employability evaluation. Unassessed components are explicitly marked NOT_ASSESSED."""
    __tablename__ = "placement_readiness_states"
    __table_args__ = (
        UniqueConstraint("student_profile_id", name="uq_student_placement_readiness"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    career_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("career_catalogs.id", ondelete="SET NULL"), nullable=True
    )

    technical_readiness: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    assessment_readiness: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    project_evidence_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    communication_readiness: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    resume_readiness: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    interview_readiness: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    career_alignment: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)

    overall_status: Mapped[str] = mapped_column(
        String(32), default="not_yet_assessed", nullable=False
    )  # not_yet_assessed, assessed, needs_portfolio, placement_ready
    component_statuses: Mapped[Dict[str, str]] = mapped_column(
        JSON, default=dict, nullable=False
    )  # e.g., {"technical": "assessed", "communication": "not_assessed"}

    algorithm_version: Mapped[str] = mapped_column(String(20), default="v1", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    student_profile: Mapped["StudentAcademicProfile"] = relationship("StudentAcademicProfile")  # noqa: F821
    career: Mapped[Optional["CareerCatalog"]] = relationship("CareerCatalog")  # noqa: F821
