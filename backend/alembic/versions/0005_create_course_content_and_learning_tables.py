"""Create Domain 4 tables for Course Delivery, Curriculum Structure & Learning Content Engine

Revision ID: 0005_create_learning_tables
Revises: 0004_create_profiles_tables
Create Date: 2026-10-05 18:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0005_create_learning_tables"
down_revision: Union[str, None] = "0004_create_profiles_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Course Contents
    op.create_table(
        "course_contents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("course_id", sa.String(length=36), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("course_catalog_id", sa.String(length=36), sa.ForeignKey("course_catalogs.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("short_description", sa.String(length=500), nullable=True),
        sa.Column("detailed_description", sa.Text(), nullable=True),
        sa.Column("learning_objectives", sa.JSON(), nullable=True),
        sa.Column("target_audience", sa.String(length=255), nullable=True),
        sa.Column("difficulty", sa.String(length=50), nullable=False, server_default="intermediate"),
        sa.Column("estimated_duration", sa.String(length=100), nullable=True),
        sa.Column("language", sa.String(length=50), nullable=False, server_default="English"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("author_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("owner_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 2. Course Content Versions
    op.create_table(
        "course_content_versions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("course_content_id", sa.String(length=36), sa.ForeignKey("course_contents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("snapshot_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("course_content_id", "version_number", name="uq_course_content_version_num"),
    )

    # 3. Curriculums
    op.create_table(
        "curriculums",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("course_content_id", sa.String(length=36), sa.ForeignKey("course_contents.id", ondelete="CASCADE"), nullable=False, unique=True, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("ordering_type", sa.String(length=50), nullable=False, server_default="sequential"),
        sa.Column("estimated_duration", sa.String(length=100), nullable=True),
        sa.Column("learning_objectives", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 4. Modules
    op.create_table(
        "modules",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("curriculum_id", sa.String(length=36), sa.ForeignKey("curriculums.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_minutes", sa.Integer(), nullable=True),
        sa.Column("learning_objectives", sa.JSON(), nullable=True),
        sa.Column("prerequisites", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("curriculum_id", "order_index", name="uq_module_curriculum_order"),
    )

    # 5. Lessons
    op.create_table(
        "lessons",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("module_id", sa.String(length=36), sa.ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("lesson_type", sa.String(length=50), nullable=False, server_default="text"),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_minutes", sa.Integer(), nullable=True, server_default="15"),
        sa.Column("learning_objectives", sa.JSON(), nullable=True),
        sa.Column("prerequisites", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("content_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("module_id", "order_index", name="uq_lesson_module_order"),
    )

    # 6. Lesson Content Blocks
    op.create_table(
        "lesson_content_blocks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("lesson_id", sa.String(length=36), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("block_type", sa.String(length=50), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("media_url", sa.String(length=1024), nullable=True),
        sa.Column("block_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("lesson_id", "order_index", name="uq_block_lesson_order"),
    )

    # 7. Learning Objectives
    op.create_table(
        "learning_objectives",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("course_content_id", sa.String(length=36), sa.ForeignKey("course_contents.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("lesson_id", sa.String(length=36), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("measurable_outcome", sa.Text(), nullable=True),
        sa.Column("taxonomy_level", sa.String(length=50), nullable=True),
        sa.Column("is_ai_generated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("teacher_approved", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 8. Concepts
    op.create_table(
        "concepts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column("slug", sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("discipline_id", sa.String(length=36), sa.ForeignKey("academic_disciplines.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("difficulty", sa.String(length=50), nullable=False, server_default="intermediate"),
        sa.Column("parent_concept_id", sa.String(length=36), sa.ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 9. Concept Prerequisites
    op.create_table(
        "concept_prerequisites",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("concept_id", sa.String(length=36), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("prerequisite_concept_id", sa.String(length=36), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("relationship_type", sa.String(length=50), nullable=False, server_default="prerequisite"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("concept_id", "prerequisite_concept_id", name="uq_concept_prerequisite"),
    )

    # 10. Lesson Concepts
    op.create_table(
        "lesson_concepts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("lesson_id", sa.String(length=36), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("concept_id", sa.String(length=36), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("importance", sa.String(length=50), nullable=False, server_default="primary"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("lesson_id", "concept_id", name="uq_lesson_concept"),
    )

    # 11. Concept Skills
    op.create_table(
        "concept_skills",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("concept_id", sa.String(length=36), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("skill_id", sa.String(length=36), sa.ForeignKey("skill_catalogs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("expected_level", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("concept_id", "skill_id", name="uq_concept_skill"),
    )

    # 12. Lesson Skills
    op.create_table(
        "lesson_skills",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("lesson_id", sa.String(length=36), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("skill_id", sa.String(length=36), sa.ForeignKey("skill_catalogs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("importance", sa.String(length=50), nullable=False, server_default="medium"),
        sa.Column("expected_level", sa.String(length=50), nullable=True),
        sa.Column("evidence_type", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("lesson_id", "skill_id", name="uq_lesson_skill"),
    )

    # 13. Course Skills
    op.create_table(
        "course_skills",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("course_content_id", sa.String(length=36), sa.ForeignKey("course_contents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("skill_id", sa.String(length=36), sa.ForeignKey("skill_catalogs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("importance", sa.String(length=50), nullable=False, server_default="primary"),
        sa.Column("expected_level", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("course_content_id", "skill_id", name="uq_course_skill"),
    )

    # 14. Learning Resources
    op.create_table(
        "learning_resources",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("resource_type", sa.String(length=50), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=True),
        sa.Column("url", sa.String(length=1024), nullable=True),
        sa.Column("provider", sa.String(length=100), nullable=True, server_default="local"),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("file_metadata", sa.JSON(), nullable=True),
        sa.Column("access_level", sa.String(length=50), nullable=False, server_default="course_only"),
        sa.Column("copyright_license", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("current_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 15. Resource Versions
    op.create_table(
        "resource_versions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("resource_id", sa.String(length=36), sa.ForeignKey("learning_resources.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=True),
        sa.Column("url", sa.String(length=1024), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("uploaded_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.UniqueConstraint("resource_id", "version_number", name="uq_resource_version_num"),
    )

    # 16. Lesson Resources
    op.create_table(
        "lesson_resources",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("lesson_id", sa.String(length=36), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("resource_id", sa.String(length=36), sa.ForeignKey("learning_resources.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("lesson_id", "resource_id", name="uq_lesson_resource"),
    )

    # 17. Content Reviews
    op.create_table(
        "content_reviews",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("course_content_id", sa.String(length=36), sa.ForeignKey("course_contents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("version_id", sa.String(length=36), sa.ForeignKey("course_content_versions.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("submitted_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("reviewed_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="submitted"),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 18. Content Review Comments
    op.create_table(
        "content_review_comments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("review_id", sa.String(length=36), sa.ForeignKey("content_reviews.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("author_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("module_id", sa.String(length=36), sa.ForeignKey("modules.id", ondelete="SET NULL"), nullable=True),
        sa.Column("lesson_id", sa.String(length=36), sa.ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 19. Lesson Progress
    op.create_table(
        "lesson_progress",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("lesson_id", sa.String(length=36), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("course_offering_id", sa.String(length=36), sa.ForeignKey("course_offerings.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("content_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="not_started"),
        sa.Column("completion_percentage", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("time_spent_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("student_profile_id", "lesson_id", "course_offering_id", name="uq_student_lesson_offering_progress"),
    )

    # 20. Course Progress
    op.create_table(
        "course_progress",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("course_offering_id", sa.String(length=36), sa.ForeignKey("course_offerings.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("course_content_id", sa.String(length=36), sa.ForeignKey("course_contents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("content_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("completed_lessons", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_required_lessons", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_modules", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_modules", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("percentage", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("student_profile_id", "course_offering_id", name="uq_student_course_offering_progress"),
    )

    # 21. Student Bookmarks
    op.create_table(
        "student_bookmarks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("student_profile_id", "target_type", "target_id", name="uq_student_bookmark"),
    )

    # 22. Student Learning Notes
    op.create_table(
        "student_learning_notes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_private", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("student_learning_notes")
    op.drop_table("student_bookmarks")
    op.drop_table("course_progress")
    op.drop_table("lesson_progress")
    op.drop_table("content_review_comments")
    op.drop_table("content_reviews")
    op.drop_table("lesson_resources")
    op.drop_table("resource_versions")
    op.drop_table("learning_resources")
    op.drop_table("course_skills")
    op.drop_table("lesson_skills")
    op.drop_table("concept_skills")
    op.drop_table("lesson_concepts")
    op.drop_table("concept_prerequisites")
    op.drop_table("concepts")
    op.drop_table("learning_objectives")
    op.drop_table("lesson_content_blocks")
    op.drop_table("lessons")
    op.drop_table("modules")
    op.drop_table("curriculums")
    op.drop_table("course_content_versions")
    op.drop_table("course_contents")
