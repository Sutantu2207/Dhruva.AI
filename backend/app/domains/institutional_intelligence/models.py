"""Database models for Institutional Analytics, Faculty Grading Workflows & Departmental Intelligence domain."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Dict, Any
from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    Numeric,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class AcademicInterventionSignal(Base):
    """Deterministic, explainable early intervention signal detecting observable academic distress."""
    __tablename__ = "academic_intervention_signals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    student_profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    course_offering_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("course_offerings.id", ondelete="SET NULL"), index=True, nullable=True
    )
    signal_type: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False
    )  # repeated_assessment_failures, persistent_low_concept_mastery, overdue_reviews, incomplete_coursework, weak_prerequisite_mastery, insufficient_evidence, prolonged_inactivity
    severity: Mapped[str] = mapped_column(
        String(32), default="medium", index=True, nullable=False
    )  # low, medium, high, urgent
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    evidence_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    recommended_action: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="detected", index=True, nullable=False
    )  # detected, acknowledged, assigned, intervention_created, dismissed, resolved

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    dismiss_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    intervention_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("student_interventions.id", ondelete="SET NULL"), nullable=True
    )
    algorithm_version: Mapped[str] = mapped_column(String(32), default="v1.0.0-deterministic", nullable=False)

    # Relationships
    student_profile: Mapped["StudentAcademicProfile"] = relationship(  # noqa: F821
        "StudentAcademicProfile", foreign_keys=[student_profile_id]
    )
    course_offering: Mapped[Optional["CourseOffering"]] = relationship(  # noqa: F821
        "CourseOffering", foreign_keys=[course_offering_id]
    )
    acknowledged_by: Mapped[Optional["User"]] = relationship(  # noqa: F821
        "User", foreign_keys=[acknowledged_by_user_id]
    )
    intervention: Mapped[Optional["StudentIntervention"]] = relationship(  # noqa: F821
        "StudentIntervention", foreign_keys=[intervention_id]
    )


class EvaluationRegradeAudit(Base):
    """Immutable audit trail of manual score adjustments and rubric revisions."""
    __tablename__ = "evaluation_regrade_audits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evaluation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessment_evaluations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    evaluator_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    previous_marks: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    new_marks: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    regraded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    evaluation: Mapped["AssessmentEvaluation"] = relationship("AssessmentEvaluation")  # noqa: F821
    evaluator: Mapped["User"] = relationship("User", foreign_keys=[evaluator_id])  # noqa: F821


class InstitutionalAnalyticsSnapshot(Base):
    """Point-in-time cached aggregate analytics snapshot for cohort, course, department, or institution."""
    __tablename__ = "institutional_analytics_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    scope_type: Mapped[str] = mapped_column(
        String(32), index=True, nullable=False
    )  # institution, department, course_offering, cohort
    scope_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    metric_payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(32), default="v1.0.0-deterministic", nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
