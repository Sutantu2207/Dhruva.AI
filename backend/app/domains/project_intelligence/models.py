"""Database models for Domain 8: Project Intelligence, Evidence Graph & Portfolio Engine."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Float,
    Integer,
    Text,
    JSON,
    UniqueConstraint,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ProjectConcept(Base):
    """Bridge connecting a student project to demonstrated concepts in Concept DAG."""
    __tablename__ = "project_concepts"
    __table_args__ = (
        UniqueConstraint("project_id", "concept_id", name="uq_project_concept_pair"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    concept_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    demonstrated_level: Mapped[str] = mapped_column(
        String(32), default="proficient", nullable=False
    )  # developing, proficient, mastered
    verification_status: Mapped[str] = mapped_column(
        String(32), default="unverified", nullable=False
    )  # unverified, verified
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    project: Mapped["StudentProject"] = relationship("StudentProject", back_populates="project_concepts")  # noqa: F821
    concept: Mapped["Concept"] = relationship("Concept")  # noqa: F821


class ProjectEvidence(Base):
    """Immutable or auditable artifact piece proving practical demonstration of technical capabilities."""
    __tablename__ = "project_evidence_items"
    __table_args__ = (
        CheckConstraint("evidence_strength >= 0.0 AND evidence_strength <= 1.0", name="chk_evidence_strength_range"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    student_profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_academic_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    evidence_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # repository, commit, pull_request, deployment, documentation, demo, screenshot, video, test_report, architecture_diagram, faculty_review, mentor_review, assessment, project_submission
    source: Mapped[str] = mapped_column(
        String(50),
        default="github",
        nullable=False,
    )  # github, gitlab, url, file_upload, internal
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    verification_status: Mapped[str] = mapped_column(
        String(32),
        default="submitted",
        nullable=False,
        index=True,
    )  # unverified, submitted, under_review, verified, rejected, expired
    verified_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    evidence_strength: Mapped[float] = mapped_column(Float, default=0.80, nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    algorithm_version: Mapped[str] = mapped_column(String(20), default="v1.0.0-deterministic", nullable=False)

    project: Mapped["StudentProject"] = relationship("StudentProject", back_populates="evidence_items")  # noqa: F821
    student_profile: Mapped["StudentAcademicProfile"] = relationship("StudentAcademicProfile")  # noqa: F821
    verified_by: Mapped[Optional["User"]] = relationship("User")  # noqa: F821


class ProjectReview(Base):
    """Structured rubric evaluation of a student project submitted by authorized faculty or mentors."""
    __tablename__ = "project_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    reviewer_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    review_type: Mapped[str] = mapped_column(
        String(32), default="faculty", nullable=False
    )  # faculty, mentor, peer

    # 10 Configurable Rubric Dimensions (each scored 0 to 100)
    technical_depth: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)
    problem_solving: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)
    code_quality: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)
    architecture_quality: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)
    documentation_quality: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)
    testing_quality: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)
    practical_application: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)
    originality: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)
    student_contribution_score: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)
    professional_presentation: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)

    overall_score: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)
    rubric_breakdown: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decision: Mapped[str] = mapped_column(
        String(32), default="approved", nullable=False
    )  # approved, rejected, revisions_requested
    is_finalized: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    project: Mapped["StudentProject"] = relationship("StudentProject", back_populates="reviews")  # noqa: F821
    reviewer: Mapped["User"] = relationship("User")  # noqa: F821


class PortfolioIntelligenceSnapshot(Base):
    """Deterministic snapshot assessing student portfolio health, completeness, and career alignment."""
    __tablename__ = "portfolio_intelligence_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_academic_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    overall_health_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="assessed", nullable=False
    )  # assessed, insufficient_evidence

    # Granular Health Dimensions (0 - 100)
    technical_depth: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    project_diversity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    evidence_quality: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    documentation_quality: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    career_alignment: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    professional_presence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    verification_coverage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    completeness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    missing_sections: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    dimension_explanations: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    algorithm_version: Mapped[str] = mapped_column(String(20), default="v1.0.0-deterministic", nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    student_profile: Mapped["StudentAcademicProfile"] = relationship("StudentAcademicProfile")  # noqa: F821
