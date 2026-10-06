"""Alembic migration 0011: Create adaptive remediation, diagnostic, outcome, snapshot and accreditation tables.

Revision ID: 0011_create_adaptive_remediation
Revises: 0010_create_institutional_analytics
Create Date: 2026-10-06 12:45:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0011_create_adaptive_remediation"
down_revision: Union[str, None] = "0010_create_institutional_analytics"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. remediation_plans
    op.create_table(
        "remediation_plans",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("originating_signal_id", sa.String(length=36), sa.ForeignKey("academic_intervention_signals.id", ondelete="SET NULL"), nullable=True),
        sa.Column("originating_intervention_id", sa.String(length=36), sa.ForeignKey("student_interventions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("target_concept_id", sa.String(length=36), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_skill_id", sa.String(length=36), sa.ForeignKey("skill_catalogs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("target_course_offering_id", sa.String(length=36), sa.ForeignKey("course_offerings.id", ondelete="SET NULL"), nullable=True),
        sa.Column("diagnosis_type", sa.String(length=64), nullable=False),
        sa.Column("diagnosis_reason", sa.Text(), nullable=False),
        sa.Column("priority_score", sa.Numeric(precision=5, scale=4), server_default="0.5000", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="recommended", nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), unique=True, nullable=False),
        sa.Column("algorithm_version", sa.String(length=32), server_default="remediation-v1.0.0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("faculty_override_reason", sa.Text(), nullable=True),
        sa.Column("faculty_reviewer_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.CheckConstraint("priority_score >= 0.0 AND priority_score <= 1.0", name="chk_remediation_priority_score_range"),
    )
    op.create_index("ix_remediation_plans_student_profile_id", "remediation_plans", ["student_profile_id"])
    op.create_index("ix_remediation_plans_originating_signal_id", "remediation_plans", ["originating_signal_id"])
    op.create_index("ix_remediation_plans_originating_intervention_id", "remediation_plans", ["originating_intervention_id"])
    op.create_index("ix_remediation_plans_target_concept_id", "remediation_plans", ["target_concept_id"])
    op.create_index("ix_remediation_plans_target_skill_id", "remediation_plans", ["target_skill_id"])
    op.create_index("ix_remediation_plans_target_course_offering_id", "remediation_plans", ["target_course_offering_id"])
    op.create_index("ix_remediation_plans_diagnosis_type", "remediation_plans", ["diagnosis_type"])
    op.create_index("ix_remediation_plans_status", "remediation_plans", ["status"])
    op.create_index("ix_remediation_plans_idempotency_key", "remediation_plans", ["idempotency_key"], unique=True)

    # 2. remediation_plan_steps
    op.create_table(
        "remediation_plan_steps",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("remediation_plan_id", sa.String(length=36), sa.ForeignKey("remediation_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sequence_order", sa.Integer(), nullable=False),
        sa.Column("step_type", sa.String(length=32), nullable=False),
        sa.Column("concept_id", sa.String(length=36), sa.ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("lesson_id", sa.String(length=36), sa.ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True),
        sa.Column("resource_id", sa.String(length=36), sa.ForeignKey("learning_resources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assessment_id", sa.String(length=36), sa.ForeignKey("assessments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("required", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("scaffold_level", sa.Integer(), server_default="1", nullable=False),
        sa.Column("completion_status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result_summary", sa.JSON(), nullable=True),
        sa.UniqueConstraint("remediation_plan_id", "sequence_order", name="uq_remediation_plan_step_seq"),
    )
    op.create_index("ix_remediation_plan_steps_remediation_plan_id", "remediation_plan_steps", ["remediation_plan_id"])
    op.create_index("ix_remediation_plan_steps_concept_id", "remediation_plan_steps", ["concept_id"])
    op.create_index("ix_remediation_plan_steps_lesson_id", "remediation_plan_steps", ["lesson_id"])
    op.create_index("ix_remediation_plan_steps_resource_id", "remediation_plan_steps", ["resource_id"])
    op.create_index("ix_remediation_plan_steps_assessment_id", "remediation_plan_steps", ["assessment_id"])
    op.create_index("ix_remediation_plan_steps_completion_status", "remediation_plan_steps", ["completion_status"])

    # 3. remediation_diagnoses
    op.create_table(
        "remediation_diagnoses",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("remediation_plan_id", sa.String(length=36), sa.ForeignKey("remediation_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("concept_id", sa.String(length=36), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("mastery_before", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("confidence_before", sa.Numeric(precision=5, scale=4), server_default="0.0000", nullable=False),
        sa.Column("retention_before", sa.Numeric(precision=5, scale=4), server_default="1.0000", nullable=False),
        sa.Column("prerequisite_readiness", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("failure_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("overdue_review_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("recent_performance", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("diagnosis_category", sa.String(length=64), nullable=False),
        sa.Column("diagnosis_reason", sa.Text(), nullable=False),
        sa.Column("explanation_payload", sa.JSON(), nullable=False),
        sa.Column("algorithm_version", sa.String(length=32), server_default="remediation-v1.0.0", nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_remediation_diagnoses_remediation_plan_id", "remediation_diagnoses", ["remediation_plan_id"])
    op.create_index("ix_remediation_diagnoses_concept_id", "remediation_diagnoses", ["concept_id"])

    # 4. remediation_attempts
    op.create_table(
        "remediation_attempts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("remediation_plan_step_id", sa.String(length=36), sa.ForeignKey("remediation_plan_steps.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attempt_number", sa.Integer(), server_default="1", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("completion_percentage", sa.Numeric(precision=5, scale=2), server_default="0.00", nullable=False),
        sa.Column("outcome", sa.String(length=32), server_default="in_progress", nullable=False),
        sa.Column("evidence_generated", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("remediation_plan_step_id", "attempt_number", name="uq_remediation_attempt_num"),
    )
    op.create_index("ix_remediation_attempts_step_id", "remediation_attempts", ["remediation_plan_step_id"])
    op.create_index("ix_remediation_attempts_student_profile_id", "remediation_attempts", ["student_profile_id"])

    # 5. remediation_outcomes
    op.create_table(
        "remediation_outcomes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("remediation_plan_id", sa.String(length=36), sa.ForeignKey("remediation_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("concept_id", sa.String(length=36), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mastery_before", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("confidence_before", sa.Numeric(precision=5, scale=4), server_default="0.0000", nullable=False),
        sa.Column("retention_before", sa.Numeric(precision=5, scale=4), server_default="1.0000", nullable=False),
        sa.Column("assessment_score_before", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("mastery_after", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("confidence_after", sa.Numeric(precision=5, scale=4), server_default="0.0000", nullable=False),
        sa.Column("retention_after", sa.Numeric(precision=5, scale=4), server_default="1.0000", nullable=False),
        sa.Column("assessment_score_after", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("improvement_delta", sa.Numeric(precision=6, scale=4), server_default="0.0000", nullable=False),
        sa.Column("outcome_status", sa.String(length=32), nullable=False),
        sa.Column("closure_decision", sa.String(length=32), server_default="CONTINUE", nullable=False),
        sa.Column("closure_reason", sa.Text(), nullable=False),
        sa.Column("algorithm_version", sa.String(length=32), server_default="remediation-v1.0.0", nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_remediation_outcomes_remediation_plan_id", "remediation_outcomes", ["remediation_plan_id"])
    op.create_index("ix_remediation_outcomes_concept_id", "remediation_outcomes", ["concept_id"])
    op.create_index("ix_remediation_outcomes_outcome_status", "remediation_outcomes", ["outcome_status"])

    # 6. remediation_snapshots
    op.create_table(
        "remediation_snapshots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scope_type", sa.String(length=32), nullable=False),
        sa.Column("scope_id", sa.String(length=36), nullable=False),
        sa.Column("metric_payload", sa.JSON(), nullable=False),
        sa.Column("source_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("algorithm_version", sa.String(length=32), server_default="remediation-v1.0.0", nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_remediation_snapshots_institution_id", "remediation_snapshots", ["institution_id"])
    op.create_index("ix_remediation_snapshots_scope_type", "remediation_snapshots", ["scope_type"])
    op.create_index("ix_remediation_snapshots_scope_id", "remediation_snapshots", ["scope_id"])

    # 7. accreditation_evidence_snapshots
    op.create_table(
        "accreditation_evidence_snapshots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("framework", sa.String(length=32), nullable=False),
        sa.Column("criterion", sa.String(length=64), nullable=False),
        sa.Column("metric_code", sa.String(length=64), nullable=False),
        sa.Column("metric_payload", sa.JSON(), nullable=False),
        sa.Column("source_domain", sa.String(length=64), server_default="Domain 10: Adaptive Remediation", nullable=False),
        sa.Column("source_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("algorithm_version", sa.String(length=32), server_default="remediation-v1.0.0", nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_accreditation_evidence_snapshots_institution_id", "accreditation_evidence_snapshots", ["institution_id"])
    op.create_index("ix_accreditation_evidence_snapshots_framework", "accreditation_evidence_snapshots", ["framework"])
    op.create_index("ix_accreditation_evidence_snapshots_criterion", "accreditation_evidence_snapshots", ["criterion"])
    op.create_index("ix_accreditation_evidence_snapshots_metric_code", "accreditation_evidence_snapshots", ["metric_code"])

    # 8. remediation_content_gaps
    op.create_table(
        "remediation_content_gaps",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("concept_id", sa.String(length=36), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", sa.String(length=36), sa.ForeignKey("courses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("demand_count", sa.Integer(), server_default="1", nullable=False),
        sa.Column("gap_type", sa.String(length=32), server_default="NO_APPROVED_LESSON", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="unresolved", nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("institution_id", "concept_id", name="uq_content_gap_institution_concept"),
    )
    op.create_index("ix_remediation_content_gaps_institution_id", "remediation_content_gaps", ["institution_id"])
    op.create_index("ix_remediation_content_gaps_concept_id", "remediation_content_gaps", ["concept_id"])
    op.create_index("ix_remediation_content_gaps_status", "remediation_content_gaps", ["status"])


def downgrade() -> None:
    op.drop_table("remediation_content_gaps")
    op.drop_table("accreditation_evidence_snapshots")
    op.drop_table("remediation_snapshots")
    op.drop_table("remediation_outcomes")
    op.drop_table("remediation_attempts")
    op.drop_table("remediation_diagnoses")
    op.drop_table("remediation_plan_steps")
    op.drop_table("remediation_plans")
