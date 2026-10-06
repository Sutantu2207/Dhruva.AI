"""SQLAlchemy Models for Domain 6: Knowledge State, Concept Mastery & Spaced Repetition."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    String,
    Text,
    Integer,
    Numeric,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class StudentConceptKnowledgeState(Base):
    """Authoritative persistent knowledge state per (student, canonical concept).
    
    Guarantees at most ONE authoritative active knowledge state per student and concept.
    Mastery and retention are strictly decoupled:
    - current_mastery represents stable learned competency [0.0, 1.0] (or None if insufficient evidence)
    - retention_estimate represents current memory recall probability [0.0, 1.0]
    """
    __tablename__ = "student_concept_knowledge_states"
    __table_args__ = (
        UniqueConstraint("student_profile_id", "concept_id", name="uq_student_concept_state"),
        CheckConstraint(
            "(current_mastery IS NULL) OR (current_mastery >= 0.0 AND current_mastery <= 1.0)",
            name="chk_mastery_range",
        ),
        CheckConstraint(
            "confidence >= 0.0 AND confidence <= 1.0",
            name="chk_confidence_range",
        ),
        CheckConstraint(
            "retention_estimate >= 0.0 AND retention_estimate <= 1.0",
            name="chk_retention_range",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_academic_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    concept_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Core Deterministic Metrics
    current_mastery: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)  # None = unknown / insufficient evidence
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    retention_estimate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("1.0000"), nullable=False)

    # State & Trend Classification
    state: Mapped[str] = mapped_column(String(30), default="unknown", index=True, nullable=False)
    # unknown, introduced, developing, proficient, mastered, at_risk
    trend: Mapped[str] = mapped_column(String(30), default="insufficient_data", nullable=False)
    # strongly_improving, improving, stable, declining, strongly_declining, insufficient_data

    # Observation Provenance
    evidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    first_evidence_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_evidence_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_successful_evidence_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failed_evidence_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Prerequisite Context
    prerequisite_readiness: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    prerequisite_health: Mapped[str] = mapped_column(String(30), default="unknown", nullable=False)
    # healthy, partial, weak, unknown

    algorithm_version: Mapped[str] = mapped_column(String(20), default="v1", nullable=False)

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

    # Relationships
    student_profile: Mapped["StudentAcademicProfile"] = relationship("StudentAcademicProfile")
    concept: Mapped["Concept"] = relationship("Concept")
    history_entries: Mapped[List["KnowledgeStateHistory"]] = relationship(
        "KnowledgeStateHistory",
        back_populates="knowledge_state",
        cascade="all, delete-orphan",
        order_by="KnowledgeStateHistory.timestamp.desc()",
        lazy="selectin",
    )


class KnowledgeStateHistory(Base):
    """Append-only audit ledger of every knowledge state recalculation."""
    __tablename__ = "knowledge_state_histories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    knowledge_state_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_concept_knowledge_states.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    student_profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_academic_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    concept_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    previous_mastery: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    new_mastery: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    change: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    retention_estimate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    state: Mapped[str] = mapped_column(String(30), nullable=False)
    trend: Mapped[str] = mapped_column(String(30), nullable=False)

    trigger: Mapped[str] = mapped_column(String(50), nullable=False)
    # assessment_evidence, practice_evidence, recall_evidence, manual_recalculation, scheduled_decay, system_rebuild
    algorithm_version: Mapped[str] = mapped_column(String(20), default="v1", nullable=False)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    knowledge_state: Mapped["StudentConceptKnowledgeState"] = relationship(
        "StudentConceptKnowledgeState", back_populates="history_entries"
    )


class ConceptEvidenceProcessing(Base):
    """Idempotency tracking ledger ensuring each Domain 5 ConceptEvidence is processed at most once."""
    __tablename__ = "concept_evidence_processings"
    __table_args__ = (
        UniqueConstraint("evidence_id", name="uq_evidence_processing_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evidence_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("concept_evidences.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    student_profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_academic_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    concept_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    evidence_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(20), default="v1", nullable=False)

    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )


class ConceptReviewState(Base):
    """Authoritative Spaced Repetition (SM-2) schedule state per (student, concept)."""
    __tablename__ = "concept_review_states"
    __table_args__ = (
        UniqueConstraint("student_profile_id", "concept_id", name="uq_student_concept_review_state"),
        CheckConstraint("repetition >= 0", name="chk_sm2_repetition"),
        CheckConstraint("interval_days >= 1", name="chk_sm2_interval"),
        CheckConstraint("ease_factor >= 1.3000", name="chk_sm2_ease_floor"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_academic_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    concept_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # SM-2 Parameters
    repetition: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ease_factor: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("2.5000"), nullable=False)
    interval_days: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_review_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    last_quality: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0 to 5

    review_status: Mapped[str] = mapped_column(String(30), default="upcoming", index=True, nullable=False)
    # due, upcoming, overdue, completed

    algorithm_version: Mapped[str] = mapped_column(String(20), default="sm2-v1", nullable=False)

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

    student_profile: Mapped["StudentAcademicProfile"] = relationship("StudentAcademicProfile")
    concept: Mapped["Concept"] = relationship("Concept")
    review_history: Mapped[List["ConceptReviewHistory"]] = relationship(
        "ConceptReviewHistory",
        back_populates="review_state",
        cascade="all, delete-orphan",
        order_by="ConceptReviewHistory.reviewed_at.desc()",
        lazy="selectin",
    )


class ConceptReviewHistory(Base):
    """Append-only audit record of every completed spaced repetition review event."""
    __tablename__ = "concept_review_histories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    review_state_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("concept_review_states.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    student_profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_academic_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    concept_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    quality: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-5
    previous_interval: Mapped[int] = mapped_column(Integer, nullable=False)
    new_interval: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_ease: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    new_ease: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)

    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    trigger: Mapped[str] = mapped_column(String(50), default="recall_session", nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(20), default="sm2-v1", nullable=False)

    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    review_state: Mapped["ConceptReviewState"] = relationship(
        "ConceptReviewState", back_populates="review_history"
    )


class LearningPrioritySnapshot(Base):
    """Computed learning priority rankings and machine-readable reason codes."""
    __tablename__ = "learning_priority_snapshots"
    __table_args__ = (
        UniqueConstraint("student_profile_id", "concept_id", name="uq_student_concept_priority"),
        CheckConstraint(
            "priority_score >= 0.0 AND priority_score <= 1.0",
            name="chk_priority_range",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_academic_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    concept_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    priority_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)  # [0.0000, 1.0000]
    reason_codes: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    # MASTERY_LOW, RETENTION_LOW, REVIEW_OVERDUE, REVIEW_DUE, PREREQUISITE_WEAK, RECENT_FAILURE, INSUFFICIENT_EVIDENCE, MASTERY_DECLINING

    mastery_gap: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    retention_risk: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    prerequisite_readiness: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("1.0000"), nullable=False)

    recommended_task_type: Mapped[str] = mapped_column(String(50), default="review", nullable=False)
    # review, practice, lesson, assessment
    reference_lesson_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    reference_assessment_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    algorithm_version: Mapped[str] = mapped_column(String(20), default="v1", nullable=False)

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    student_profile: Mapped["StudentAcademicProfile"] = relationship("StudentAcademicProfile")
    concept: Mapped["Concept"] = relationship("Concept")


class MasteryAdjustment(Base):
    """Institutional audit log of manual teacher/admin mastery adjustments."""
    __tablename__ = "mastery_adjustments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_academic_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    concept_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    previous_calculated_mastery: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    adjusted_mastery: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    adjusted_by_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
