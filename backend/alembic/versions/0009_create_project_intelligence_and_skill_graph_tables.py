"""Create Domain 8 tables for Project Intelligence, Evidence Graph & Portfolio Engine

Revision ID: 0009_create_project_intelligence
Revises: 0008_complete_skill_intelligence
Create Date: 2026-10-06 10:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0009_create_project_intelligence"
down_revision: Union[str, None] = "0008_complete_skill_intelligence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Alter student_projects table with Domain 8 extensions
    op.add_column("student_projects", sa.Column("slug", sa.String(length=255), nullable=True))
    op.create_index("ix_student_projects_slug", "student_projects", ["slug"])
    op.add_column("student_projects", sa.Column("short_description", sa.String(length=500), nullable=True))
    op.add_column("student_projects", sa.Column("problem_statement", sa.Text(), nullable=True))
    op.add_column("student_projects", sa.Column("solution", sa.Text(), nullable=True))
    op.add_column("student_projects", sa.Column("live_url", sa.String(length=500), nullable=True))
    op.add_column("student_projects", sa.Column("visibility", sa.String(length=32), server_default="private", nullable=False))
    op.add_column("student_projects", sa.Column("verification_status", sa.String(length=32), server_default="unverified", nullable=False))
    op.create_index("ix_student_projects_verification_status", "student_projects", ["verification_status"])
    op.add_column("student_projects", sa.Column("team_size", sa.Integer(), server_default="1", nullable=False))
    op.add_column("student_projects", sa.Column("contribution_description", sa.Text(), nullable=True))
    op.add_column("student_projects", sa.Column("contribution_percentage", sa.Float(), nullable=True))
    op.add_column("student_projects", sa.Column("modules_contributed", sa.JSON(), nullable=True))
    op.add_column("student_projects", sa.Column("quality_score", sa.Float(), nullable=True))
    op.add_column("student_projects", sa.Column("quality_breakdown", sa.JSON(), nullable=True))
    op.add_column("student_projects", sa.Column("career_relevance_score", sa.Float(), nullable=True))
    op.add_column("student_projects", sa.Column("career_relevance_category", sa.String(length=32), nullable=True))

    # 2. Alter student_project_skills table
    op.add_column("student_project_skills", sa.Column("claimed_level", sa.String(length=32), server_default="intermediate", nullable=False))
    op.add_column("student_project_skills", sa.Column("observed_level", sa.String(length=32), nullable=True))
    op.add_column("student_project_skills", sa.Column("evidence_strength", sa.Float(), server_default="0.5", nullable=False))
    op.add_column("student_project_skills", sa.Column("verification_status", sa.String(length=32), server_default="unverified", nullable=False))
    op.add_column("student_project_skills", sa.Column("verified_by_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True))
    op.add_column("student_project_skills", sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("student_project_skills", sa.Column("source", sa.String(length=50), server_default="student_claim", nullable=False))
    op.add_column("student_project_skills", sa.Column("notes", sa.Text(), nullable=True))

    # 3. Alter student_portfolios table
    op.add_column("student_portfolios", sa.Column("slug", sa.String(length=128), nullable=True))
    op.create_unique_constraint("uq_student_portfolio_slug", "student_portfolios", ["slug"])
    op.add_column("student_portfolios", sa.Column("theme", sa.String(length=64), server_default="modern", nullable=False))
    op.add_column("student_portfolios", sa.Column("featured_certification_ids", sa.JSON(), nullable=True))
    op.add_column("student_portfolios", sa.Column("featured_achievement_ids", sa.JSON(), nullable=True))
    op.add_column("student_portfolios", sa.Column("contact_email", sa.String(length=255), nullable=True))
    op.add_column("student_portfolios", sa.Column("social_links", sa.JSON(), nullable=True))

    # 4. Table project_concepts
    op.create_table(
        "project_concepts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("student_projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("concept_id", sa.String(length=36), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("demonstrated_level", sa.String(length=32), server_default="proficient", nullable=False),
        sa.Column("verification_status", sa.String(length=32), server_default="unverified", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_id", "concept_id", name="uq_project_concept_pair"),
    )

    # 5. Table project_evidence_items
    op.create_table(
        "project_evidence_items",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("student_projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("evidence_type", sa.String(length=50), nullable=False, index=True),
        sa.Column("source", sa.String(length=50), server_default="github", nullable=False),
        sa.Column("source_reference", sa.String(length=500), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("verification_status", sa.String(length=32), server_default="submitted", nullable=False, index=True),
        sa.Column("verified_by_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence_strength", sa.Float(), server_default="0.80", nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("algorithm_version", sa.String(length=20), server_default="v1.0.0-deterministic", nullable=False),
        sa.CheckConstraint("evidence_strength >= 0.0 AND evidence_strength <= 1.0", name="chk_evidence_strength_range"),
    )

    # 6. Table project_reviews
    op.create_table(
        "project_reviews",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("student_projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("reviewer_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("review_type", sa.String(length=32), server_default="faculty", nullable=False),
        sa.Column("technical_depth", sa.Float(), server_default="70.0", nullable=False),
        sa.Column("problem_solving", sa.Float(), server_default="70.0", nullable=False),
        sa.Column("code_quality", sa.Float(), server_default="70.0", nullable=False),
        sa.Column("architecture_quality", sa.Float(), server_default="70.0", nullable=False),
        sa.Column("documentation_quality", sa.Float(), server_default="70.0", nullable=False),
        sa.Column("testing_quality", sa.Float(), server_default="70.0", nullable=False),
        sa.Column("practical_application", sa.Float(), server_default="70.0", nullable=False),
        sa.Column("originality", sa.Float(), server_default="70.0", nullable=False),
        sa.Column("student_contribution_score", sa.Float(), server_default="70.0", nullable=False),
        sa.Column("professional_presentation", sa.Float(), server_default="70.0", nullable=False),
        sa.Column("overall_score", sa.Float(), server_default="70.0", nullable=False),
        sa.Column("rubric_breakdown", sa.JSON(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("decision", sa.String(length=32), server_default="approved", nullable=False),
        sa.Column("is_finalized", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 7. Table portfolio_intelligence_snapshots
    op.create_table(
        "portfolio_intelligence_snapshots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("overall_health_score", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="assessed", nullable=False),
        sa.Column("technical_depth", sa.Float(), nullable=True),
        sa.Column("project_diversity", sa.Float(), nullable=True),
        sa.Column("evidence_quality", sa.Float(), nullable=True),
        sa.Column("documentation_quality", sa.Float(), nullable=True),
        sa.Column("career_alignment", sa.Float(), nullable=True),
        sa.Column("professional_presence", sa.Float(), nullable=True),
        sa.Column("verification_coverage", sa.Float(), nullable=True),
        sa.Column("completeness_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("missing_sections", sa.JSON(), nullable=True),
        sa.Column("dimension_explanations", sa.JSON(), nullable=True),
        sa.Column("algorithm_version", sa.String(length=20), server_default="v1.0.0-deterministic", nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("portfolio_intelligence_snapshots")
    op.drop_table("project_reviews")
    op.drop_table("project_evidence_items")
    op.drop_table("project_concepts")

    # Drop columns on student_portfolios
    op.drop_constraint("uq_student_portfolio_slug", "student_portfolios", type_="unique")
    op.drop_column("student_portfolios", "social_links")
    op.drop_column("student_portfolios", "contact_email")
    op.drop_column("student_portfolios", "featured_achievement_ids")
    op.drop_column("student_portfolios", "featured_certification_ids")
    op.drop_column("student_portfolios", "theme")
    op.drop_column("student_portfolios", "slug")

    # Drop columns on student_project_skills
    op.drop_column("student_project_skills", "notes")
    op.drop_column("student_project_skills", "source")
    op.drop_column("student_project_skills", "verified_at")
    op.drop_column("student_project_skills", "verified_by_user_id")
    op.drop_column("student_project_skills", "verification_status")
    op.drop_column("student_project_skills", "evidence_strength")
    op.drop_column("student_project_skills", "observed_level")
    op.drop_column("student_project_skills", "claimed_level")

    # Drop columns on student_projects
    op.drop_index("ix_student_projects_verification_status", table_name="student_projects")
    op.drop_index("ix_student_projects_slug", table_name="student_projects")
    op.drop_column("student_projects", "career_relevance_category")
    op.drop_column("student_projects", "career_relevance_score")
    op.drop_column("student_projects", "quality_breakdown")
    op.drop_column("student_projects", "quality_score")
    op.drop_column("student_projects", "modules_contributed")
    op.drop_column("student_projects", "contribution_percentage")
    op.drop_column("student_projects", "contribution_description")
    op.drop_column("student_projects", "team_size")
    op.drop_column("student_projects", "verification_status")
    op.drop_column("student_projects", "visibility")
    op.drop_column("student_projects", "live_url")
    op.drop_column("student_projects", "solution")
    op.drop_column("student_projects", "problem_statement")
    op.drop_column("student_projects", "short_description")
    op.drop_column("student_projects", "slug")
