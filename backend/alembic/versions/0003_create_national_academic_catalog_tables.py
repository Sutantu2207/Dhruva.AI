"""Create national academic taxonomy and India-wide academic catalog tables

Revision ID: 0003_create_catalog_tables
Revises: 0002_create_academic_tables
Create Date: 2026-10-05 17:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003_create_catalog_tables"
down_revision: Union[str, None] = "0002_create_academic_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Academic Catalog Versions
    op.create_table(
        "academic_catalog_versions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("release_name", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("deprecated_date", sa.Date(), nullable=True),
        sa.Column("release_notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("version", name="uq_catalog_version_code"),
    )
    op.create_index("ix_academic_catalog_versions_version", "academic_catalog_versions", ["version"])

    # 2. Academic Catalog Sources
    op.create_table(
        "academic_catalog_sources",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("authority_type", sa.String(length=50), nullable=False, server_default="statutory_body"),
        sa.Column("jurisdiction", sa.String(length=100), nullable=False, server_default="India"),
        sa.Column("website_url", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("code", name="uq_catalog_source_code"),
    )
    op.create_index("ix_academic_catalog_sources_code", "academic_catalog_sources", ["code"])

    # 3. Academic Disciplines
    op.create_table(
        "academic_disciplines",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parent_discipline_id", sa.String(length=36), sa.ForeignKey("academic_disciplines.id", ondelete="SET NULL"), nullable=True),
        sa.Column("aliases", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("version", sa.String(length=50), nullable=False, server_default="v1.0"),
        sa.Column("source_id", sa.String(length=36), sa.ForeignKey("academic_catalog_sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("code", name="uq_discipline_code"),
        sa.UniqueConstraint("slug", name="uq_discipline_slug"),
    )
    op.create_index("ix_academic_disciplines_code", "academic_disciplines", ["code"])
    op.create_index("ix_academic_disciplines_slug", "academic_disciplines", ["slug"])
    op.create_index("ix_academic_disciplines_name", "academic_disciplines", ["name"])

    # 4. Degree Types
    op.create_table(
        "degree_types",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=True),
        sa.Column("level", sa.String(length=50), nullable=False),
        sa.Column("typical_duration_years", sa.Float(), nullable=True),
        sa.Column("min_credits", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("source_id", sa.String(length=36), sa.ForeignKey("academic_catalog_sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("code", name="uq_degree_type_code"),
        sa.UniqueConstraint("name", name="uq_degree_type_name"),
    )
    op.create_index("ix_degree_types_code", "degree_types", ["code"])
    op.create_index("ix_degree_types_level", "degree_types", ["level"])

    # 5. Program Catalogs
    op.create_table(
        "program_catalogs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("short_name", sa.String(length=50), nullable=True),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("discipline_id", sa.String(length=36), sa.ForeignKey("academic_disciplines.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("degree_type_id", sa.String(length=36), sa.ForeignKey("degree_types.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("duration_years", sa.Float(), nullable=False, server_default="4.0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("aliases", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("version", sa.String(length=50), nullable=False, server_default="v1.0"),
        sa.Column("source_id", sa.String(length=36), sa.ForeignKey("academic_catalog_sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("code", name="uq_program_catalog_code"),
        sa.UniqueConstraint("slug", name="uq_program_catalog_slug"),
    )
    op.create_index("ix_program_catalogs_code", "program_catalogs", ["code"])
    op.create_index("ix_program_catalogs_slug", "program_catalogs", ["slug"])
    op.create_index("ix_program_catalogs_name", "program_catalogs", ["name"])
    op.create_index("ix_program_catalogs_discipline_id", "program_catalogs", ["discipline_id"])
    op.create_index("ix_program_catalogs_degree_type_id", "program_catalogs", ["degree_type_id"])

    # 6. Program Specializations
    op.create_table(
        "program_specializations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("program_catalog_id", sa.String(length=36), sa.ForeignKey("program_catalogs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("aliases", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("program_catalog_id", "code", name="uq_specialization_prog_code"),
        sa.UniqueConstraint("program_catalog_id", "slug", name="uq_specialization_prog_slug"),
    )
    op.create_index("ix_program_specializations_code", "program_specializations", ["code"])
    op.create_index("ix_program_specializations_name", "program_specializations", ["name"])

    # 7. Course Catalogs
    op.create_table(
        "course_catalogs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("discipline_id", sa.String(length=36), sa.ForeignKey("academic_disciplines.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("credits", sa.Float(), nullable=False, server_default="3.0"),
        sa.Column("level", sa.String(length=50), nullable=False, server_default="undergraduate"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("prerequisites", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("aliases", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("version", sa.String(length=50), nullable=False, server_default="v1.0"),
        sa.Column("source_id", sa.String(length=36), sa.ForeignKey("academic_catalog_sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("code", name="uq_course_catalog_code"),
        sa.UniqueConstraint("slug", name="uq_course_catalog_slug"),
    )
    op.create_index("ix_course_catalogs_code", "course_catalogs", ["code"])
    op.create_index("ix_course_catalogs_slug", "course_catalogs", ["slug"])
    op.create_index("ix_course_catalogs_title", "course_catalogs", ["title"])
    op.create_index("ix_course_catalogs_discipline_id", "course_catalogs", ["discipline_id"])

    # 8. Skill Catalogs
    op.create_table(
        "skill_catalogs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False, server_default="technical"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("aliases", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("version", sa.String(length=50), nullable=False, server_default="v1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("code", name="uq_skill_catalog_code"),
        sa.UniqueConstraint("slug", name="uq_skill_catalog_slug"),
    )
    op.create_index("ix_skill_catalogs_code", "skill_catalogs", ["code"])
    op.create_index("ix_skill_catalogs_slug", "skill_catalogs", ["slug"])
    op.create_index("ix_skill_catalogs_name", "skill_catalogs", ["name"])
    op.create_index("ix_skill_catalogs_category", "skill_catalogs", ["category"])

    # 9. Career Catalogs
    op.create_table(
        "career_catalogs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("industry_sector", sa.String(length=100), nullable=False, server_default="Information Technology"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("aliases", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("version", sa.String(length=50), nullable=False, server_default="v1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("code", name="uq_career_catalog_code"),
        sa.UniqueConstraint("slug", name="uq_career_catalog_slug"),
    )
    op.create_index("ix_career_catalogs_code", "career_catalogs", ["code"])
    op.create_index("ix_career_catalogs_slug", "career_catalogs", ["slug"])
    op.create_index("ix_career_catalogs_title", "career_catalogs", ["title"])
    op.create_index("ix_career_catalogs_industry_sector", "career_catalogs", ["industry_sector"])

    # 10. Program Skill Mappings
    op.create_table(
        "program_skill_mappings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("program_catalog_id", sa.String(length=36), sa.ForeignKey("program_catalogs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_catalog_id", sa.String(length=36), sa.ForeignKey("skill_catalogs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relevance_weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("is_core", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("program_catalog_id", "skill_catalog_id", name="uq_prog_skill_pair"),
    )
    op.create_index("ix_program_skill_mappings_program_id", "program_skill_mappings", ["program_catalog_id"])
    op.create_index("ix_program_skill_mappings_skill_id", "program_skill_mappings", ["skill_catalog_id"])

    # 11. Course Skill Mappings
    op.create_table(
        "course_skill_mappings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("course_catalog_id", sa.String(length=36), sa.ForeignKey("course_catalogs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_catalog_id", sa.String(length=36), sa.ForeignKey("skill_catalogs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("depth_level", sa.String(length=50), nullable=False, server_default="intermediate"),
        sa.Column("relevance_weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("course_catalog_id", "skill_catalog_id", name="uq_course_skill_pair"),
    )
    op.create_index("ix_course_skill_mappings_course_id", "course_skill_mappings", ["course_catalog_id"])
    op.create_index("ix_course_skill_mappings_skill_id", "course_skill_mappings", ["skill_catalog_id"])

    # 12. Career Skill Mappings
    op.create_table(
        "career_skill_mappings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("career_catalog_id", sa.String(length=36), sa.ForeignKey("career_catalogs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_catalog_id", sa.String(length=36), sa.ForeignKey("skill_catalogs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("importance", sa.String(length=50), nullable=False, server_default="required"),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("career_catalog_id", "skill_catalog_id", name="uq_career_skill_pair"),
    )
    op.create_index("ix_career_skill_mappings_career_id", "career_skill_mappings", ["career_catalog_id"])
    op.create_index("ix_career_skill_mappings_skill_id", "career_skill_mappings", ["skill_catalog_id"])

    # 13. Program Career Mappings
    op.create_table(
        "program_career_mappings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("program_catalog_id", sa.String(length=36), sa.ForeignKey("program_catalogs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("career_catalog_id", sa.String(length=36), sa.ForeignKey("career_catalogs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alignment_score", sa.Float(), nullable=False, server_default="0.8"),
        sa.Column("is_primary_path", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("program_catalog_id", "career_catalog_id", name="uq_prog_career_pair"),
    )
    op.create_index("ix_program_career_mappings_program_id", "program_career_mappings", ["program_catalog_id"])
    op.create_index("ix_program_career_mappings_career_id", "program_career_mappings", ["career_catalog_id"])

    # 14. Institution Program Mappings
    op.create_table(
        "institution_program_mappings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("institution_program_id", sa.String(length=36), sa.ForeignKey("programs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("national_program_id", sa.String(length=36), sa.ForeignKey("program_catalogs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("local_code", sa.String(length=50), nullable=True),
        sa.Column("local_name", sa.String(length=255), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("mapping_confidence", sa.String(length=50), nullable=False, server_default="verified"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("institution_id", "institution_program_id", "national_program_id", name="uq_inst_prog_nat_mapping"),
    )
    op.create_index("ix_institution_program_mappings_inst_id", "institution_program_mappings", ["institution_id"])
    op.create_index("ix_institution_program_mappings_inst_prog_id", "institution_program_mappings", ["institution_program_id"])
    op.create_index("ix_institution_program_mappings_nat_prog_id", "institution_program_mappings", ["national_program_id"])

    # 15. Institution Course Mappings
    op.create_table(
        "institution_course_mappings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("institution_course_id", sa.String(length=36), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("national_course_id", sa.String(length=36), sa.ForeignKey("course_catalogs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("local_code", sa.String(length=50), nullable=True),
        sa.Column("local_name", sa.String(length=255), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("mapping_confidence", sa.String(length=50), nullable=False, server_default="verified"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("institution_id", "institution_course_id", "national_course_id", name="uq_inst_course_nat_mapping"),
    )
    op.create_index("ix_institution_course_mappings_inst_id", "institution_course_mappings", ["institution_id"])
    op.create_index("ix_institution_course_mappings_inst_course_id", "institution_course_mappings", ["institution_course_id"])
    op.create_index("ix_institution_course_mappings_nat_course_id", "institution_course_mappings", ["national_course_id"])

    # 16. Catalog Import Jobs
    op.create_table(
        "catalog_import_jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("source_id", sa.String(length=36), sa.ForeignKey("academic_catalog_sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("is_dry_run", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("total_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("report_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("failed_records", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("initiated_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_catalog_import_jobs_status", "catalog_import_jobs", ["status"])
    op.create_index("ix_catalog_import_jobs_entity_type", "catalog_import_jobs", ["entity_type"])


def downgrade() -> None:
    op.drop_table("catalog_import_jobs")
    op.drop_table("institution_course_mappings")
    op.drop_table("institution_program_mappings")
    op.drop_table("program_career_mappings")
    op.drop_table("career_skill_mappings")
    op.drop_table("course_skill_mappings")
    op.drop_table("program_skill_mappings")
    op.drop_table("career_catalogs")
    op.drop_table("skill_catalogs")
    op.drop_table("course_catalogs")
    op.drop_table("program_specializations")
    op.drop_table("program_catalogs")
    op.drop_table("degree_types")
    op.drop_table("academic_disciplines")
    op.drop_table("academic_catalog_sources")
    op.drop_table("academic_catalog_versions")
