"""Create Domain 7 tables for Skill Intelligence, Career Trajectories & Placement Readiness

Revision ID: 0008_complete_skill_intelligence
Revises: 0007_create_knowledge_state_tables
Create Date: 2026-10-05 20:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0008_complete_skill_intelligence"
down_revision: Union[str, None] = "0007_create_knowledge_state_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Student Skill Intelligence States
    op.create_table(
        "student_skill_intelligence_states",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("skill_id", sa.String(length=36), sa.ForeignKey("skill_catalogs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("observed_proficiency", sa.Numeric(precision=5, scale=4), default=0.0000, nullable=False),
        sa.Column("self_reported_proficiency", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("verified_proficiency", sa.Numeric(precision=5, scale=4), default=0.0000, nullable=False),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), default=0.0000, nullable=False),
        sa.Column("evidence_count", sa.Integer(), default=0, nullable=False),
        sa.Column("verified_evidence_count", sa.Integer(), default=0, nullable=False),
        sa.Column("assessment_evidence_count", sa.Integer(), default=0, nullable=False),
        sa.Column("project_evidence_count", sa.Integer(), default=0, nullable=False),
        sa.Column("course_evidence_count", sa.Integer(), default=0, nullable=False),
        sa.Column("certification_evidence_count", sa.Integer(), default=0, nullable=False),
        sa.Column("concept_mastery_contribution", sa.Numeric(precision=5, scale=4), default=0.0000, nullable=False),
        sa.Column("verification_status", sa.String(length=32), default="unverified", nullable=False, index=True),
        sa.Column("proficiency_tier", sa.String(length=32), default="exposure", nullable=False, index=True),
        sa.Column("algorithm_version", sa.String(length=20), default="v1", nullable=False),
        sa.Column("last_evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("student_profile_id", "skill_id", name="uq_student_skill_intelligence"),
        sa.CheckConstraint("observed_proficiency >= 0.0 AND observed_proficiency <= 1.0", name="chk_skill_observed_range"),
        sa.CheckConstraint("verified_proficiency >= 0.0 AND verified_proficiency <= 1.0", name="chk_skill_verified_range"),
        sa.CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="chk_skill_confidence_range"),
    )

    # 2. Student Skill Evidence Records
    op.create_table(
        "student_skill_evidence_records",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("skill_id", sa.String(length=36), sa.ForeignKey("skill_catalogs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("source_type", sa.String(length=50), nullable=False, index=True),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("evidence_score", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("evidence_weight", sa.Numeric(precision=5, scale=4), default=1.0000, nullable=False),
        sa.Column("is_verified", sa.Boolean(), default=False, nullable=False),
        sa.Column("provenance_details", sa.JSON(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 3. Student Career Readiness States
    op.create_table(
        "student_career_readiness_states",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("career_id", sa.String(length=36), sa.ForeignKey("career_catalogs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("readiness_score", sa.Numeric(precision=5, scale=4), default=0.0000, nullable=False, index=True),
        sa.Column("fit_score", sa.Numeric(precision=5, scale=4), default=0.0000, nullable=False),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), default=0.0000, nullable=False),
        sa.Column("required_skill_coverage", sa.Numeric(precision=5, scale=4), default=0.0000, nullable=False),
        sa.Column("preferred_skill_coverage", sa.Numeric(precision=5, scale=4), default=0.0000, nullable=False),
        sa.Column("critical_skill_coverage", sa.Numeric(precision=5, scale=4), default=0.0000, nullable=False),
        sa.Column("critical_gaps_count", sa.Integer(), default=0, nullable=False),
        sa.Column("strengths_count", sa.Integer(), default=0, nullable=False),
        sa.Column("developing_count", sa.Integer(), default=0, nullable=False),
        sa.Column("has_sufficient_catalog_data", sa.Boolean(), default=True, nullable=False),
        sa.Column("status", sa.String(length=32), default="assessed", nullable=False),
        sa.Column("explanation_breakdown", sa.JSON(), nullable=True),
        sa.Column("algorithm_version", sa.String(length=20), default="v1", nullable=False),
        sa.Column("last_evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("student_profile_id", "career_id", name="uq_student_career_readiness"),
        sa.CheckConstraint("readiness_score >= 0.0 AND readiness_score <= 1.0", name="chk_career_readiness_range"),
        sa.CheckConstraint("fit_score >= 0.0 AND fit_score <= 1.0", name="chk_career_fit_range"),
        sa.CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="chk_career_confidence_range"),
    )

    # 4. Career Trajectories
    op.create_table(
        "career_trajectories",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("career_id", sa.String(length=36), sa.ForeignKey("career_catalogs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("status", sa.String(length=32), default="in_progress", nullable=False),
        sa.Column("total_steps", sa.Integer(), default=0, nullable=False),
        sa.Column("completed_steps", sa.Integer(), default=0, nullable=False),
        sa.Column("algorithm_version", sa.String(length=20), default="v1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("student_profile_id", "career_id", name="uq_student_career_trajectory"),
    )

    # 5. Career Trajectory Steps
    op.create_table(
        "career_trajectory_steps",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("trajectory_id", sa.String(length=36), sa.ForeignKey("career_trajectories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.String(length=36), sa.ForeignKey("skill_catalogs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("step_type", sa.String(length=50), default="concept_mastery", nullable=False),
        sa.Column("priority", sa.String(length=32), default="medium", nullable=False),
        sa.Column("status", sa.String(length=32), default="not_started", nullable=False),
        sa.Column("target_proficiency", sa.Numeric(precision=5, scale=4), default=0.7000, nullable=False),
        sa.Column("current_proficiency", sa.Numeric(precision=5, scale=4), default=0.0000, nullable=False),
        sa.Column("gap_size", sa.Numeric(precision=5, scale=4), default=0.0000, nullable=False),
        sa.Column("reference_course_id", sa.String(length=36), sa.ForeignKey("course_catalogs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reference_lesson_id", sa.String(length=36), sa.ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reference_concept_id", sa.String(length=36), sa.ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reference_assessment_id", sa.String(length=36), sa.ForeignKey("assessments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 6. Placement Readiness States
    op.create_table(
        "placement_readiness_states",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("career_id", sa.String(length=36), sa.ForeignKey("career_catalogs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("technical_readiness", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("assessment_readiness", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("project_evidence_score", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("communication_readiness", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("resume_readiness", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("interview_readiness", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("career_alignment", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("overall_status", sa.String(length=32), default="not_yet_assessed", nullable=False),
        sa.Column("component_statuses", sa.JSON(), nullable=False),
        sa.Column("algorithm_version", sa.String(length=20), default="v1", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("student_profile_id", name="uq_student_placement_readiness"),
    )


def downgrade() -> None:
    op.drop_table("placement_readiness_states")
    op.drop_table("career_trajectory_steps")
    op.drop_table("career_trajectories")
    op.drop_table("student_career_readiness_states")
    op.drop_table("student_skill_evidence_records")
    op.drop_table("student_skill_intelligence_states")
