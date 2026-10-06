"""Create Domain 9 tables for Institutional Analytics, Grading Workflows & Early Intervention

Revision ID: 0010_create_institutional_analytics
Revises: 0009_create_project_intelligence
Create Date: 2026-10-06 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0010_create_institutional_analytics"
down_revision: Union[str, None] = "0009_create_project_intelligence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Table academic_intervention_signals
    op.create_table(
        "academic_intervention_signals",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_offering_id", sa.String(length=36), sa.ForeignKey("course_offerings.id", ondelete="SET NULL"), nullable=True),
        sa.Column("signal_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), server_default="medium", nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("evidence_data", sa.JSON(), nullable=False),
        sa.Column("recommended_action", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="detected", nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_by_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("dismiss_reason", sa.Text(), nullable=True),
        sa.Column("intervention_id", sa.String(length=36), sa.ForeignKey("student_interventions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("algorithm_version", sa.String(length=32), server_default="v1.0.0-deterministic", nullable=False),
    )
    op.create_index("ix_academic_intervention_signals_institution_id", "academic_intervention_signals", ["institution_id"])
    op.create_index("ix_academic_intervention_signals_student_profile_id", "academic_intervention_signals", ["student_profile_id"])
    op.create_index("ix_academic_intervention_signals_course_offering_id", "academic_intervention_signals", ["course_offering_id"])
    op.create_index("ix_academic_intervention_signals_signal_type", "academic_intervention_signals", ["signal_type"])
    op.create_index("ix_academic_intervention_signals_severity", "academic_intervention_signals", ["severity"])
    op.create_index("ix_academic_intervention_signals_status", "academic_intervention_signals", ["status"])

    # 2. Table evaluation_regrade_audits
    op.create_table(
        "evaluation_regrade_audits",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("evaluation_id", sa.String(length=36), sa.ForeignKey("assessment_evaluations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evaluator_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("previous_marks", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("new_marks", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("regraded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_evaluation_regrade_audits_evaluation_id", "evaluation_regrade_audits", ["evaluation_id"])
    op.create_index("ix_evaluation_regrade_audits_evaluator_id", "evaluation_regrade_audits", ["evaluator_id"])

    # 3. Table institutional_analytics_snapshots
    op.create_table(
        "institutional_analytics_snapshots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scope_type", sa.String(length=32), nullable=False),
        sa.Column("scope_id", sa.String(length=36), nullable=False),
        sa.Column("metric_payload", sa.JSON(), nullable=False),
        sa.Column("algorithm_version", sa.String(length=32), server_default="v1.0.0-deterministic", nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_institutional_analytics_snapshots_institution_id", "institutional_analytics_snapshots", ["institution_id"])
    op.create_index("ix_institutional_analytics_snapshots_scope_type", "institutional_analytics_snapshots", ["scope_type"])
    op.create_index("ix_institutional_analytics_snapshots_scope_id", "institutional_analytics_snapshots", ["scope_id"])


def downgrade() -> None:
    op.drop_table("institutional_analytics_snapshots")
    op.drop_table("evaluation_regrade_audits")
    op.drop_table("academic_intervention_signals")
