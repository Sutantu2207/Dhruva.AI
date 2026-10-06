"""Create Domain 5 tables for Assessment Engine, Question Banks, Evaluation & Evidence

Revision ID: 0006_create_assessment_tables
Revises: 0005_create_learning_tables
Create Date: 2026-10-05 19:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0006_create_assessment_tables"
down_revision: Union[str, None] = "0005_create_learning_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Question Banks
    op.create_table(
        "question_banks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("owner_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("department_id", sa.String(length=36), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("course_id", sa.String(length=36), sa.ForeignKey("courses.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("visibility", sa.String(length=30), nullable=False, server_default="institution"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 2. Evaluation Rubrics
    op.create_table(
        "evaluation_rubrics",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 3. Rubric Criteria
    op.create_table(
        "rubric_criteria",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("rubric_id", sa.String(length=36), sa.ForeignKey("evaluation_rubrics.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("max_points", sa.Numeric(precision=10, scale=2), nullable=False, server_default="10.00"),
        sa.Column("weight", sa.Numeric(precision=5, scale=2), nullable=False, server_default="1.00"),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 4. Assessment Bank Questions
    op.create_table(
        "assessment_bank_questions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("bank_id", sa.String(length=36), sa.ForeignKey("question_banks.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("question_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("difficulty", sa.String(length=30), nullable=False, server_default="medium"),
        sa.Column("current_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("author_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("reviewer_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 5. Question Versions
    op.create_table(
        "question_versions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("question_id", sa.String(length=36), sa.ForeignKey("assessment_bank_questions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("points", sa.Numeric(precision=10, scale=2), nullable=False, server_default="1.00"),
        sa.Column("negative_marks", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"),
        sa.Column("estimated_seconds", sa.Integer(), nullable=True),
        sa.Column("difficulty", sa.String(length=30), nullable=False, server_default="medium"),
        sa.Column("rubric_id", sa.String(length=36), sa.ForeignKey("evaluation_rubrics.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("evaluation_config", sa.JSON(), nullable=True),
        sa.Column("created_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("question_id", "version_number", name="uq_question_version_num"),
    )

    # 6. Question Options
    op.create_table(
        "question_options",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("question_version_id", sa.String(length=36), sa.ForeignKey("question_versions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("option_text", sa.Text(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("metadata_payload", sa.JSON(), nullable=True),
        sa.UniqueConstraint("question_version_id", "order_index", name="uq_question_option_order"),
    )

    # 7. Question Concepts
    op.create_table(
        "question_concepts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("question_version_id", sa.String(length=36), sa.ForeignKey("question_versions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("concept_id", sa.String(length=36), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("importance", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("weight", sa.Numeric(precision=5, scale=2), nullable=False, server_default="1.00"),
        sa.UniqueConstraint("question_version_id", "concept_id", name="uq_question_concept"),
    )

    # 8. Question Skills
    op.create_table(
        "question_skills",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("question_version_id", sa.String(length=36), sa.ForeignKey("question_versions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("skill_id", sa.String(length=36), sa.ForeignKey("skill_catalogs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("weight", sa.Numeric(precision=5, scale=2), nullable=False, server_default="1.00"),
        sa.Column("evidence_type", sa.String(length=50), nullable=False, server_default="assessment"),
        sa.UniqueConstraint("question_version_id", "skill_id", name="uq_question_skill"),
    )

    # 9. Coding Configurations
    op.create_table(
        "coding_configurations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("question_version_id", sa.String(length=36), sa.ForeignKey("question_versions.id", ondelete="CASCADE"), nullable=False, unique=True, index=True),
        sa.Column("language", sa.String(length=50), nullable=False, server_default="python"),
        sa.Column("starter_code", sa.Text(), nullable=True),
        sa.Column("function_signature", sa.Text(), nullable=True),
        sa.Column("time_limit_ms", sa.Integer(), nullable=False, server_default="2000"),
        sa.Column("memory_limit_mb", sa.Integer(), nullable=False, server_default="256"),
        sa.Column("constraints_text", sa.Text(), nullable=True),
        sa.Column("input_format", sa.Text(), nullable=True),
        sa.Column("output_format", sa.Text(), nullable=True),
    )

    # 10. Coding Test Cases
    op.create_table(
        "coding_test_cases",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("coding_config_id", sa.String(length=36), sa.ForeignKey("coding_configurations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("input_data", sa.Text(), nullable=False),
        sa.Column("expected_output", sa.Text(), nullable=False),
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("points_weight", sa.Numeric(precision=5, scale=2), nullable=False, server_default="1.00"),
    )

    # 11. Assessments
    op.create_table(
        "assessments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("course_offering_id", sa.String(length=36), sa.ForeignKey("course_offerings.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("assessment_type", sa.String(length=50), nullable=False, server_default="quiz"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("total_marks", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"),
        sa.Column("passing_marks", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"),
        sa.Column("attempts_allowed", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("randomization_config", sa.JSON(), nullable=True),
        sa.Column("feedback_policy", sa.String(length=50), nullable=False, server_default="after_submission"),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("late_submission_allowed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("current_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("reviewed_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 12. Assessment Blueprints
    op.create_table(
        "assessment_blueprints",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("assessment_id", sa.String(length=36), sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("total_questions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rules_config", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 13. Assessment Versions
    op.create_table(
        "assessment_versions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("assessment_id", sa.String(length=36), sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("total_marks", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"),
        sa.Column("passing_marks", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("feedback_policy", sa.String(length=50), nullable=False, server_default="after_submission"),
        sa.Column("rules_snapshot", sa.JSON(), nullable=True),
        sa.Column("is_frozen", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("assessment_id", "version_number", name="uq_assessment_version_num"),
    )

    # 14. Assessment Version Questions
    op.create_table(
        "assessment_version_questions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("assessment_version_id", sa.String(length=36), sa.ForeignKey("assessment_versions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("question_version_id", sa.String(length=36), sa.ForeignKey("question_versions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("section_name", sa.String(length=100), nullable=False, server_default="Default"),
        sa.Column("custom_points", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("custom_negative_marks", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.UniqueConstraint("assessment_version_id", "question_version_id", name="uq_assessment_version_question"),
    )

    # 15. Assessment Attempts
    op.create_table(
        "assessment_attempts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("assessment_version_id", sa.String(length=36), sa.ForeignKey("assessment_versions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="not_started"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("percentage", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("is_passed", sa.Boolean(), nullable=True),
        sa.Column("result_status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("attempt_token", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("assessment_version_id", "student_profile_id", "attempt_number", name="uq_attempt_version_student_num"),
    )

    # 16. Assessment Responses
    op.create_table(
        "assessment_responses",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("attempt_id", sa.String(length=36), sa.ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("question_version_id", sa.String(length=36), sa.ForeignKey("question_versions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("response_type", sa.String(length=50), nullable=False),
        sa.Column("response_payload", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_flagged", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("attempt_id", "question_version_id", name="uq_attempt_question_response"),
    )

    # 17. Assessment Evaluations
    op.create_table(
        "assessment_evaluations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("attempt_id", sa.String(length=36), sa.ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("question_version_id", sa.String(length=36), sa.ForeignKey("question_versions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("awarded_marks", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"),
        sa.Column("penalty_marks", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"),
        sa.Column("max_marks", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("evaluation_type", sa.String(length=50), nullable=False, server_default="deterministic"),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("evaluator_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("attempt_id", "question_version_id", name="uq_attempt_question_eval"),
    )

    # 18. Manual Evaluations
    op.create_table(
        "manual_evaluations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("evaluation_id", sa.String(length=36), sa.ForeignKey("assessment_evaluations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("rubric_criterion_id", sa.String(length=36), sa.ForeignKey("rubric_criteria.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("awarded_points", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"),
        sa.Column("evaluator_notes", sa.Text(), nullable=True),
        sa.Column("graded_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("graded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 19. Assessment Results
    op.create_table(
        "assessment_results",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("attempt_id", sa.String(length=36), sa.ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, unique=True, index=True),
        sa.Column("total_marks_obtained", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"),
        sa.Column("maximum_marks", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"),
        sa.Column("percentage", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0.00"),
        sa.Column("grade", sa.String(length=10), nullable=True),
        sa.Column("is_passed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("released_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("comments", sa.Text(), nullable=True),
    )

    # 20. Concept Evidences
    op.create_table(
        "concept_evidences",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("concept_id", sa.String(length=36), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("question_version_id", sa.String(length=36), sa.ForeignKey("question_versions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("assessment_id", sa.String(length=36), sa.ForeignKey("assessments.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("attempt_id", sa.String(length=36), sa.ForeignKey("assessment_attempts.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("score", sa.Numeric(precision=5, scale=4), nullable=False, server_default="0.0000"),
        sa.Column("max_score", sa.Numeric(precision=5, scale=4), nullable=False, server_default="1.0000"),
        sa.Column("evidence_type", sa.String(length=50), nullable=False, server_default="assessment"),
        sa.Column("evaluation_method", sa.String(length=50), nullable=False, server_default="deterministic"),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 21. Skill Evidences
    op.create_table(
        "skill_evidences",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("skill_id", sa.String(length=36), sa.ForeignKey("skill_catalogs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("question_version_id", sa.String(length=36), sa.ForeignKey("question_versions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("assessment_id", sa.String(length=36), sa.ForeignKey("assessments.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("attempt_id", sa.String(length=36), sa.ForeignKey("assessment_attempts.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("score", sa.Numeric(precision=5, scale=4), nullable=False, server_default="0.0000"),
        sa.Column("weight", sa.Numeric(precision=5, scale=2), nullable=False, server_default="1.00"),
        sa.Column("evidence_type", sa.String(length=50), nullable=False, server_default="assessment"),
        sa.Column("evaluation_method", sa.String(length=50), nullable=False, server_default="deterministic"),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 22. Grade Schemes
    op.create_table(
        "grade_schemes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("rules_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 23. Assessment Integrity Events
    op.create_table(
        "assessment_integrity_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("attempt_id", sa.String(length=36), sa.ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("metadata_payload", sa.JSON(), nullable=True),
    )

    # 24. Assessment Reviews
    op.create_table(
        "assessment_reviews",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("assessment_id", sa.String(length=36), sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("submitted_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("reviewed_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="submitted"),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("assessment_reviews")
    op.drop_table("assessment_integrity_events")
    op.drop_table("grade_schemes")
    op.drop_table("skill_evidences")
    op.drop_table("concept_evidences")
    op.drop_table("assessment_results")
    op.drop_table("manual_evaluations")
    op.drop_table("assessment_evaluations")
    op.drop_table("assessment_responses")
    op.drop_table("assessment_attempts")
    op.drop_table("assessment_version_questions")
    op.drop_table("assessment_versions")
    op.drop_table("assessment_blueprints")
    op.drop_table("assessments")
    op.drop_table("coding_test_cases")
    op.drop_table("coding_configurations")
    op.drop_table("question_skills")
    op.drop_table("question_concepts")
    op.drop_table("question_options")
    op.drop_table("question_versions")
    op.drop_table("assessment_bank_questions")
    op.drop_table("rubric_criteria")
    op.drop_table("evaluation_rubrics")
    op.drop_table("question_banks")
