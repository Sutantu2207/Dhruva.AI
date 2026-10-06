"""Create Domain 6 tables for Knowledge State, Concept Mastery Engine & Spaced Repetition

Revision ID: 0007_create_knowledge_state_tables
Revises: 0006_create_assessment_tables
Create Date: 2026-10-05 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0007_create_knowledge_state_tables"
down_revision: Union[str, None] = "0006_create_assessment_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Student Concept Knowledge States
    op.create_table(
        "student_concept_knowledge_states",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("concept_id", sa.String(length=36), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("current_mastery", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=False, server_default="0.0000"),
        sa.Column("retention_estimate", sa.Numeric(precision=5, scale=4), nullable=False, server_default="1.0000"),
        sa.Column("state", sa.String(length=30), nullable=False, server_default="unknown", index=True),
        sa.Column("trend", sa.String(length=30), nullable=False, server_default="insufficient_data"),
        sa.Column("evidence_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_evidence_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_evidence_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_successful_evidence_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failed_evidence_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("prerequisite_readiness", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("prerequisite_health", sa.String(length=30), nullable=False, server_default="unknown"),
        sa.Column("algorithm_version", sa.String(length=20), nullable=False, server_default="v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("student_profile_id", "concept_id", name="uq_student_concept_state"),
        sa.CheckConstraint("(current_mastery IS NULL) OR (current_mastery >= 0.0 AND current_mastery <= 1.0)", name="chk_mastery_range"),
        sa.CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="chk_confidence_range"),
        sa.CheckConstraint("retention_estimate >= 0.0 AND retention_estimate <= 1.0", name="chk_retention_range"),
    )

    # 2. Knowledge State Histories (Append-Only)
    op.create_table(
        "knowledge_state_histories",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("knowledge_state_id", sa.String(length=36), sa.ForeignKey("student_concept_knowledge_states.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("concept_id", sa.String(length=36), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("previous_mastery", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("new_mastery", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("change", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("retention_estimate", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("state", sa.String(length=30), nullable=False),
        sa.Column("trend", sa.String(length=30), nullable=False),
        sa.Column("trigger", sa.String(length=50), nullable=False),
        sa.Column("algorithm_version", sa.String(length=20), nullable=False, server_default="v1"),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 3. Concept Evidence Processings (Idempotency Table)
    op.create_table(
        "concept_evidence_processings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("evidence_id", sa.String(length=36), sa.ForeignKey("concept_evidences.id", ondelete="CASCADE"), nullable=False, unique=True, index=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("concept_id", sa.String(length=36), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("evidence_score", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("algorithm_version", sa.String(length=20), nullable=False, server_default="v1"),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 4. Concept Review States (SM-2 Spaced Repetition)
    op.create_table(
        "concept_review_states",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("concept_id", sa.String(length=36), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("repetition", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ease_factor", sa.Numeric(precision=5, scale=4), nullable=False, server_default="2.5000"),
        sa.Column("interval_days", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_review_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("last_quality", sa.Integer(), nullable=True),
        sa.Column("review_status", sa.String(length=30), nullable=False, server_default="upcoming", index=True),
        sa.Column("algorithm_version", sa.String(length=20), nullable=False, server_default="sm2-v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("student_profile_id", "concept_id", name="uq_student_concept_review_state"),
        sa.CheckConstraint("repetition >= 0", name="chk_sm2_repetition"),
        sa.CheckConstraint("interval_days >= 1", name="chk_sm2_interval"),
        sa.CheckConstraint("ease_factor >= 1.3000", name="chk_sm2_ease_floor"),
    )

    # 5. Concept Review Histories (Append-Only)
    op.create_table(
        "concept_review_histories",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("review_state_id", sa.String(length=36), sa.ForeignKey("concept_review_states.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("concept_id", sa.String(length=36), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("quality", sa.Integer(), nullable=False),
        sa.Column("previous_interval", sa.Integer(), nullable=False),
        sa.Column("new_interval", sa.Integer(), nullable=False),
        sa.Column("previous_ease", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("new_ease", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("trigger", sa.String(length=50), nullable=False, server_default="recall_session"),
        sa.Column("algorithm_version", sa.String(length=20), nullable=False, server_default="sm2-v1"),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 6. Learning Priority Snapshots
    op.create_table(
        "learning_priority_snapshots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("concept_id", sa.String(length=36), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("priority_score", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("reason_codes", sa.JSON(), nullable=False),
        sa.Column("mastery_gap", sa.Numeric(precision=5, scale=4), nullable=False, server_default="0.0000"),
        sa.Column("retention_risk", sa.Numeric(precision=5, scale=4), nullable=False, server_default="0.0000"),
        sa.Column("prerequisite_readiness", sa.Numeric(precision=5, scale=4), nullable=False, server_default="1.0000"),
        sa.Column("recommended_task_type", sa.String(length=50), nullable=False, server_default="review"),
        sa.Column("reference_lesson_id", sa.String(length=36), nullable=True),
        sa.Column("reference_assessment_id", sa.String(length=36), nullable=True),
        sa.Column("algorithm_version", sa.String(length=20), nullable=False, server_default="v1"),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("student_profile_id", "concept_id", name="uq_student_concept_priority"),
        sa.CheckConstraint("priority_score >= 0.0 AND priority_score <= 1.0", name="chk_priority_range"),
    )

    # 7. Mastery Adjustments (Audited Manual Overrides)
    op.create_table(
        "mastery_adjustments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("concept_id", sa.String(length=36), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("previous_calculated_mastery", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("adjusted_mastery", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("adjusted_by_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("mastery_adjustments")
    op.drop_table("learning_priority_snapshots")
    op.drop_table("concept_review_histories")
    op.drop_table("concept_review_states")
    op.drop_table("concept_evidence_processings")
    op.drop_table("knowledge_state_histories")
    op.drop_table("student_concept_knowledge_states")
