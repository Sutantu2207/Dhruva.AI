"""SQLAlchemy Models for Domain 10: Autonomous Adaptive Remediation & Institutional Intelligence Closing."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Dict, Any, List
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
    Boolean,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


# =========================================================================
# 1. Remediation Plan
# =========================================================================

class RemediationPlan(Base):
    """Personalized, deterministic remediation recovery plan for an identified deficiency."""
    __tablename__ = "remediation_plans"
    __table_args__ = (
        CheckConstraint(
            "priority_score >= 0.0 AND priority_score <= 1.0",
            name="chk_remediation_priority_score_range",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    originating_signal_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("academic_intervention_signals.id", ondelete="SET NULL"), index=True, nullable=True
    )
    originating_intervention_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("student_interventions.id", ondelete="SET NULL"), index=True, nullable=True
    )
    target_concept_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("concepts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    target_skill_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("skill_catalogs.id", ondelete="SET NULL"), index=True, nullable=True
    )
    target_course_offering_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("course_offerings.id", ondelete="SET NULL"), index=True, nullable=True
    )

    # Deterministic Diagnosis & Reason
    diagnosis_type: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False
    )  # LOW_MASTERY, LOW_RETENTION, PREREQUISITE_GAP, REPEATED_ASSESSMENT_FAILURE, INCOMPLETE_LEARNING_PATH, MISSED_ASSESSMENT, PRACTICAL_EVIDENCE_GAP, MULTI_FACTOR
    diagnosis_reason: Mapped[str] = mapped_column(Text, nullable=False)
    priority_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.5000"), nullable=False)

    # Status Lifecycle: draft, recommended, assigned, in_progress, paused, completed, failed, closed, cancelled
    status: Mapped[str] = mapped_column(String(32), default="recommended", index=True, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(32), default="remediation-v1.0.0", nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Faculty Oversight & Overrides
    faculty_override_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    faculty_reviewer_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    student_profile: Mapped["StudentAcademicProfile"] = relationship("StudentAcademicProfile")  # noqa: F821
    originating_signal: Mapped[Optional["AcademicInterventionSignal"]] = relationship("AcademicInterventionSignal")  # noqa: F821
    originating_intervention: Mapped[Optional["StudentIntervention"]] = relationship("StudentIntervention")  # noqa: F821
    target_concept: Mapped["Concept"] = relationship("Concept")  # noqa: F821
    target_skill: Mapped[Optional["SkillCatalog"]] = relationship("SkillCatalog")  # noqa: F821
    target_course_offering: Mapped[Optional["CourseOffering"]] = relationship("CourseOffering")  # noqa: F821
    faculty_reviewer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[faculty_reviewer_id])  # noqa: F821

    steps: Mapped[List["RemediationPlanStep"]] = relationship(
        "RemediationPlanStep", back_populates="remediation_plan", cascade="all, delete-orphan", order_by="RemediationPlanStep.sequence_order", lazy="selectin"
    )
    diagnoses: Mapped[List["RemediationDiagnosis"]] = relationship(
        "RemediationDiagnosis", back_populates="remediation_plan", cascade="all, delete-orphan", lazy="selectin"
    )
    outcomes: Mapped[List["RemediationOutcome"]] = relationship(
        "RemediationOutcome", back_populates="remediation_plan", cascade="all, delete-orphan", lazy="selectin"
    )


# =========================================================================
# 2. Remediation Plan Step
# =========================================================================

class RemediationPlanStep(Base):
    """Atomic scaffolded step within a remediation plan."""
    __tablename__ = "remediation_plan_steps"
    __table_args__ = (
        UniqueConstraint("remediation_plan_id", "sequence_order", name="uq_remediation_plan_step_seq"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    remediation_plan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("remediation_plans.id", ondelete="CASCADE"), index=True, nullable=False
    )
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)
    # PREREQUISITE, MICRO_LESSON, GUIDED_PRACTICE, PRACTICE_ASSESSMENT, APPLICATION, REASSESSMENT, REFLECTION
    step_type: Mapped[str] = mapped_column(String(32), nullable=False)

    concept_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("concepts.id", ondelete="SET NULL"), index=True, nullable=True
    )
    lesson_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("lessons.id", ondelete="SET NULL"), index=True, nullable=True
    )
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("learning_resources.id", ondelete="SET NULL"), index=True, nullable=True
    )
    assessment_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("assessments.id", ondelete="SET NULL"), index=True, nullable=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    scaffold_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1 (recall) to 5 (application)

    # Completion Status: pending, in_progress, completed, skipped, failed
    completion_status: Mapped[str] = mapped_column(String(32), default="pending", index=True, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    result_summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    remediation_plan: Mapped["RemediationPlan"] = relationship("RemediationPlan", back_populates="steps")
    concept: Mapped[Optional["Concept"]] = relationship("Concept")  # noqa: F821
    lesson: Mapped[Optional["Lesson"]] = relationship("Lesson")  # noqa: F821
    resource: Mapped[Optional["LearningResource"]] = relationship("LearningResource")  # noqa: F821
    assessment: Mapped[Optional["Assessment"]] = relationship("Assessment")  # noqa: F821

    attempts: Mapped[List["RemediationAttempt"]] = relationship(
        "RemediationAttempt", back_populates="plan_step", cascade="all, delete-orphan", order_by="RemediationAttempt.attempt_number"
    )


# =========================================================================
# 3. Remediation Diagnosis (Explainable Record)
# =========================================================================

class RemediationDiagnosis(Base):
    """Deterministic snapshot of student's diagnostic profile leading to remediation."""
    __tablename__ = "remediation_diagnoses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    remediation_plan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("remediation_plans.id", ondelete="CASCADE"), index=True, nullable=False
    )
    concept_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("concepts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    evidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mastery_before: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    confidence_before: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    retention_before: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("1.0000"), nullable=False)
    prerequisite_readiness: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)

    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    overdue_review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    recent_performance: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)

    diagnosis_category: Mapped[str] = mapped_column(String(64), nullable=False)
    diagnosis_reason: Mapped[str] = mapped_column(Text, nullable=False)
    explanation_payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(32), default="remediation-v1.0.0", nullable=False)

    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    remediation_plan: Mapped["RemediationPlan"] = relationship("RemediationPlan", back_populates="diagnoses")
    concept: Mapped["Concept"] = relationship("Concept")  # noqa: F821


# =========================================================================
# 4. Remediation Attempt
# =========================================================================

class RemediationAttempt(Base):
    """Learner's attempt at an individual remediation step (e.g. micro-lesson or practice)."""
    __tablename__ = "remediation_attempts"
    __table_args__ = (
        UniqueConstraint("remediation_plan_step_id", "attempt_number", name="uq_remediation_attempt_num"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    remediation_plan_step_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("remediation_plan_steps.id", ondelete="CASCADE"), index=True, nullable=False
    )
    student_profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    completion_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), default="in_progress", nullable=False)  # in_progress, passed, failed, completed
    evidence_generated: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    plan_step: Mapped["RemediationPlanStep"] = relationship("RemediationPlanStep", back_populates="attempts")
    student_profile: Mapped["StudentAcademicProfile"] = relationship("StudentAcademicProfile")  # noqa: F821


# =========================================================================
# 5. Remediation Outcome (Closed-Loop Measurement)
# =========================================================================

class RemediationOutcome(Base):
    """Deterministic post-reassessment outcome measurement verifying observable delta."""
    __tablename__ = "remediation_outcomes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    remediation_plan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("remediation_plans.id", ondelete="CASCADE"), index=True, nullable=False
    )
    concept_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("concepts.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # Before
    mastery_before: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    confidence_before: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    retention_before: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("1.0000"), nullable=False)
    assessment_score_before: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    # After
    mastery_after: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    confidence_after: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    retention_after: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("1.0000"), nullable=False)
    assessment_score_after: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    # Improvement Delta (mastery_after - mastery_before)
    improvement_delta: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0.0000"), nullable=False)

    # Outcome Status: IMPROVED, PARTIALLY_IMPROVED, NO_SIGNIFICANT_CHANGE, REGRESSED, INSUFFICIENT_EVIDENCE
    outcome_status: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    # Closure Decision: CLOSE_SUCCESS, CONTINUE, ESCALATE
    closure_decision: Mapped[str] = mapped_column(String(32), default="CONTINUE", nullable=False)
    closure_reason: Mapped[str] = mapped_column(Text, nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(32), default="remediation-v1.0.0", nullable=False)

    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    remediation_plan: Mapped["RemediationPlan"] = relationship("RemediationPlan", back_populates="outcomes")
    concept: Mapped["Concept"] = relationship("Concept")  # noqa: F821


# =========================================================================
# 6. Remediation Institutional Aggregate Snapshot (Analytics Cache)
# =========================================================================

class RemediationSnapshot(Base):
    """Aggregated, non-authoritative analytics cache for institutional remediation performance."""
    __tablename__ = "remediation_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    scope_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)  # institution, department, course
    scope_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)

    metric_payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    source_period_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    source_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    algorithm_version: Mapped[str] = mapped_column(String(32), default="remediation-v1.0.0", nullable=False)

    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    institution: Mapped["Institution"] = relationship("Institution")  # noqa: F821


# =========================================================================
# 7. Accreditation Evidence Snapshot (NAAC/NBA Preparation)
# =========================================================================

class AccreditationEvidenceSnapshot(Base):
    """Institutional accreditation & audit-ready evidence mapping (NAAC / NBA).
    
    CRITICAL INVARIANT: This record prepares verifiable evidence mapped to criteria.
    It does NOT assert official accreditation compliance.
    """
    __tablename__ = "accreditation_evidence_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    framework: Mapped[str] = mapped_column(String(32), index=True, nullable=False)  # NAAC, NBA, NIRF, ABET
    criterion: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # e.g., "2.2.1", "Criteria 2", "CO-PO Attainment"
    metric_code: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    metric_payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    source_domain: Mapped[str] = mapped_column(String(64), default="Domain 10: Adaptive Remediation", nullable=False)
    source_period_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    source_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    algorithm_version: Mapped[str] = mapped_column(String(32), default="remediation-v1.0.0", nullable=False)

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    institution: Mapped["Institution"] = relationship("Institution")  # noqa: F821


# =========================================================================
# 8. Institutional Content Gap Record
# =========================================================================

class ContentGapRecord(Base):
    """Auditable detection of repeated remediation demand where no approved content exists."""
    __tablename__ = "remediation_content_gaps"
    __table_args__ = (
        UniqueConstraint("institution_id", "concept_id", name="uq_content_gap_institution_concept"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    concept_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("concepts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    course_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("courses.id", ondelete="SET NULL"), index=True, nullable=True
    )
    demand_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    gap_type: Mapped[str] = mapped_column(String(32), default="NO_APPROVED_LESSON", nullable=False)  # NO_APPROVED_LESSON, NO_PRACTICE_QUESTION, NO_REASSESSMENT
    status: Mapped[str] = mapped_column(String(32), default="unresolved", index=True, nullable=False)  # unresolved, acknowledged, resolved

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    institution: Mapped["Institution"] = relationship("Institution")  # noqa: F821
    concept: Mapped["Concept"] = relationship("Concept")  # noqa: F821
    course: Mapped[Optional["Course"]] = relationship("Course")  # noqa: F821
