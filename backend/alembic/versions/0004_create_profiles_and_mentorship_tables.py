"""Create Domain 3 tables for student/faculty profiles, mentorship, and bulk onboarding

Revision ID: 0004_create_profiles_tables
Revises: 0003_create_catalog_tables
Create Date: 2026-10-05 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0004_create_profiles_tables"
down_revision: Union[str, None] = "0003_create_catalog_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Student Profile Details
    op.create_table(
        "student_profile_details",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("headline", sa.String(length=255), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("learning_preferences", sa.JSON(), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("contact_phone", sa.String(length=50), nullable=True),
        sa.Column("linkedin_url", sa.String(length=255), nullable=True),
        sa.Column("github_url", sa.String(length=255), nullable=True),
        sa.Column("website_url", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_student_profile_details_profile_id", "student_profile_details", ["student_profile_id"])

    # 2. Student Academic Status History
    op.create_table(
        "student_academic_status_history",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("old_status", sa.String(length=32), nullable=False),
        sa.Column("new_status", sa.String(length=32), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("changed_by_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_student_status_history_profile_id", "student_academic_status_history", ["student_profile_id"])

    # 3. Student Skills
    op.create_table(
        "student_skills",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_catalog_id", sa.String(length=36), sa.ForeignKey("skill_catalogs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("proficiency", sa.String(length=32), nullable=False, server_default="beginner"),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="self_declared"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("verified_by_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("last_assessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("student_profile_id", "skill_catalog_id", name="uq_student_skill_catalog"),
    )
    op.create_index("ix_student_skills_profile_id", "student_skills", ["student_profile_id"])
    op.create_index("ix_student_skills_skill_catalog_id", "student_skills", ["skill_catalog_id"])

    # 4. Student Interests
    op.create_table(
        "student_interests",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("discipline_id", sa.String(length=36), sa.ForeignKey("academic_disciplines.id", ondelete="SET NULL"), nullable=True),
        sa.Column("career_catalog_id", sa.String(length=36), sa.ForeignKey("career_catalogs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("interest_title", sa.String(length=128), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_student_interests_profile_id", "student_interests", ["student_profile_id"])

    # 5. Student Career Goals
    op.create_table(
        "student_career_goals",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("career_catalog_id", sa.String(length=36), sa.ForeignKey("career_catalogs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("short_term_goals", sa.Text(), nullable=True),
        sa.Column("long_term_goals", sa.Text(), nullable=True),
        sa.Column("target_industry", sa.String(length=128), nullable=True),
        sa.Column("preferred_locations", sa.JSON(), nullable=True),
        sa.Column("target_organizations", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("student_profile_id", "career_catalog_id", name="uq_student_career_catalog"),
    )
    op.create_index("ix_student_career_goals_profile_id", "student_career_goals", ["student_profile_id"])

    # 6. Student Projects
    op.create_table(
        "student_projects",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("project_type", sa.String(length=64), nullable=False, server_default="academic"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="in_progress"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("repository_url", sa.String(length=500), nullable=True),
        sa.Column("demo_url", sa.String(length=500), nullable=True),
        sa.Column("documentation_url", sa.String(length=500), nullable=True),
        sa.Column("technologies", sa.JSON(), nullable=True),
        sa.Column("team_or_individual", sa.String(length=32), nullable=False, server_default="individual"),
        sa.Column("role", sa.String(length=128), nullable=True),
        sa.Column("outcomes", sa.Text(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("verified_by_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_student_projects_profile_id", "student_projects", ["student_profile_id"])

    # 7. Student Project Skills Bridge
    op.create_table(
        "student_project_skills",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("student_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_catalog_id", sa.String(length=36), sa.ForeignKey("skill_catalogs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("project_id", "skill_catalog_id", name="uq_project_skill_pair"),
    )
    op.create_index("ix_student_project_skills_proj_id", "student_project_skills", ["project_id"])

    # 8. Student Certifications
    op.create_table(
        "student_certifications",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("issuer", sa.String(length=255), nullable=False),
        sa.Column("credential_id", sa.String(length=128), nullable=True),
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("credential_url", sa.String(length=500), nullable=True),
        sa.Column("document_reference", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="unverified"),
        sa.Column("verified_by_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("verification_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_student_certifications_profile_id", "student_certifications", ["student_profile_id"])

    # 9. Student Achievements
    op.create_table(
        "student_achievements",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=64), nullable=False, server_default="competition"),
        sa.Column("achievement_date", sa.Date(), nullable=True),
        sa.Column("issuer_event", sa.String(length=255), nullable=True),
        sa.Column("evidence_url", sa.String(length=500), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("verified_by_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_student_achievements_profile_id", "student_achievements", ["student_profile_id"])

    # 10. Student Portfolios
    op.create_table(
        "student_portfolios",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("headline", sa.String(length=255), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("featured_project_ids", sa.JSON(), nullable=True),
        sa.Column("featured_skill_ids", sa.JSON(), nullable=True),
        sa.Column("public_visibility", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("custom_links", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_student_portfolios_profile_id", "student_portfolios", ["student_profile_id"])

    # 11. Student Resumes
    op.create_table(
        "student_resumes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("selected_project_ids", sa.JSON(), nullable=True),
        sa.Column("selected_skill_ids", sa.JSON(), nullable=True),
        sa.Column("selected_certification_ids", sa.JSON(), nullable=True),
        sa.Column("selected_achievement_ids", sa.JSON(), nullable=True),
        sa.Column("experience_entries", sa.JSON(), nullable=True),
        sa.Column("custom_sections", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_student_resumes_profile_id", "student_resumes", ["student_profile_id"])

    # 12. Teacher Profile Details
    op.create_table(
        "teacher_profile_details",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("teacher_profile_id", sa.String(length=36), sa.ForeignKey("teacher_academic_profiles.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("biography", sa.Text(), nullable=True),
        sa.Column("experience_years", sa.Float(), nullable=True),
        sa.Column("qualifications", sa.JSON(), nullable=True),
        sa.Column("expertise_areas", sa.JSON(), nullable=True),
        sa.Column("office_location", sa.String(length=128), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("contact_phone", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_teacher_profile_details_profile_id", "teacher_profile_details", ["teacher_profile_id"])

    # 13. Mentorship Relations
    op.create_table(
        "mentorship_relations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mentor_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("assignment_source", sa.String(length=32), nullable=False, server_default="admin_assigned"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("mentor_user_id", "student_profile_id", name="uq_mentor_student_pair"),
    )
    op.create_index("ix_mentorship_relations_inst", "mentorship_relations", ["institution_id"])
    op.create_index("ix_mentorship_relations_mentor", "mentorship_relations", ["mentor_user_id"])
    op.create_index("ix_mentorship_relations_student", "mentorship_relations", ["student_profile_id"])

    # 14. Mentor Groups
    op.create_table(
        "mentor_groups",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("department_id", sa.String(length=36), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("mentor_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_mentor_groups_inst", "mentor_groups", ["institution_id"])

    # 15. Mentor Group Members
    op.create_table(
        "mentor_group_members",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("mentor_group_id", sa.String(length=36), sa.ForeignKey("mentor_groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("mentor_group_id", "student_profile_id", name="uq_group_student_pair"),
    )

    # 16. Mentor Notes
    op.create_table(
        "mentor_notes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mentor_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("visibility", sa.String(length=32), nullable=False, server_default="private_mentor"),
        sa.Column("follow_up_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_mentor_notes_student", "mentor_notes", ["student_profile_id"])

    # 17. Student Interventions
    op.create_table(
        "student_interventions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("action_plan", sa.Text(), nullable=True),
        sa.Column("follow_up_date", sa.Date(), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("resolved_by_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_student_interventions_inst", "student_interventions", ["institution_id"])
    op.create_index("ix_student_interventions_student", "student_interventions", ["student_profile_id"])

    # 18. Onboarding Import Jobs
    op.create_table(
        "onboarding_import_jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("import_type", sa.String(length=32), nullable=False),
        sa.Column("initiated_by_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("is_dry_run", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("total_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("successful_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicate_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_onboarding_jobs_inst", "onboarding_import_jobs", ["institution_id"])

    # 19. Domain Audit Logs
    op.create_table(
        "domain_audit_logs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.String(length=36), nullable=True),
        sa.Column("actor_user_id", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=64), nullable=False),
        sa.Column("metadata_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_domain_audit_logs_actor", "domain_audit_logs", ["actor_user_id"])
    op.create_index("ix_domain_audit_logs_inst", "domain_audit_logs", ["institution_id"])


def downgrade() -> None:
    op.drop_table("domain_audit_logs")
    op.drop_table("onboarding_import_jobs")
    op.drop_table("student_interventions")
    op.drop_table("mentor_notes")
    op.drop_table("mentor_group_members")
    op.drop_table("mentor_groups")
    op.drop_table("mentorship_relations")
    op.drop_table("teacher_profile_details")
    op.drop_table("student_resumes")
    op.drop_table("student_portfolios")
    op.drop_table("student_achievements")
    op.drop_table("student_certifications")
    op.drop_table("student_project_skills")
    op.drop_table("student_projects")
    op.drop_table("student_career_goals")
    op.drop_table("student_interests")
    op.drop_table("student_skills")
    op.drop_table("student_academic_status_history")
    op.drop_table("student_profile_details")
