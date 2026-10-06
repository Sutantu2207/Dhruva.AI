"""Create academic management and institutional hierarchy tables

Revision ID: 0002_create_academic_tables
Revises: 0001_create_identity_tables
Create Date: 2026-10-05 16:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_create_academic_tables"
down_revision: Union[str, None] = "0001_create_identity_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Institutions
    op.create_table(
        "institutions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("email_domains", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("code", name="uq_institution_code"),
    )
    op.create_index("ix_institutions_code", "institutions", ["code"])

    # 2. Departments
    op.create_table(
        "departments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("institution_id", "code", name="uq_department_inst_code"),
    )
    op.create_index("ix_departments_institution_id", "departments", ["institution_id"])

    # 3. Programs
    op.create_table(
        "programs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("department_id", sa.String(length=36), sa.ForeignKey("departments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("degree_type", sa.String(length=50), nullable=False, server_default="B.Tech"),
        sa.Column("duration_years", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("department_id", "code", name="uq_program_dept_code"),
    )
    op.create_index("ix_programs_department_id", "programs", ["department_id"])

    # 4. Academic Years
    op.create_table(
        "academic_years",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("institution_id", "name", name="uq_academic_year_inst_name"),
    )
    op.create_index("ix_academic_years_institution_id", "academic_years", ["institution_id"])

    # 5. Semesters
    op.create_table(
        "semesters",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("academic_year_id", sa.String(length=36), sa.ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False),
        sa.Column("semester_number", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=50), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("academic_year_id", "semester_number", name="uq_semester_year_num"),
    )
    op.create_index("ix_semesters_academic_year_id", "semesters", ["academic_year_id"])

    # 6. Batches
    op.create_table(
        "batches",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("program_id", sa.String(length=36), sa.ForeignKey("programs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("admission_year", sa.Integer(), nullable=False),
        sa.Column("graduation_year", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("program_id", "label", name="uq_batch_prog_label"),
    )
    op.create_index("ix_batches_institution_id", "batches", ["institution_id"])
    op.create_index("ix_batches_program_id", "batches", ["program_id"])

    # 7. Sections
    op.create_table(
        "sections",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("batch_id", sa.String(length=36), sa.ForeignKey("batches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("batch_id", "name", name="uq_section_batch_name"),
    )
    op.create_index("ix_sections_batch_id", "sections", ["batch_id"])

    # 8. Courses
    op.create_table(
        "courses",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("department_id", sa.String(length=36), sa.ForeignKey("departments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("credits", sa.Float(), nullable=False, server_default="3.0"),
        sa.Column("course_type", sa.String(length=50), nullable=False, server_default="core"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("institution_id", "code", name="uq_course_inst_code"),
    )
    op.create_index("ix_courses_institution_id", "courses", ["institution_id"])
    op.create_index("ix_courses_department_id", "courses", ["department_id"])

    # 9. Course Offerings
    op.create_table(
        "course_offerings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("course_id", sa.String(length=36), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("academic_year_id", sa.String(length=36), sa.ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False),
        sa.Column("semester_id", sa.String(length=36), sa.ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("section_id", sa.String(length=36), sa.ForeignKey("sections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("course_id", "academic_year_id", "semester_id", "section_id", name="uq_offering_period_section"),
    )
    op.create_index("ix_course_offerings_course_id", "course_offerings", ["course_id"])
    op.create_index("ix_course_offerings_academic_year_id", "course_offerings", ["academic_year_id"])
    op.create_index("ix_course_offerings_semester_id", "course_offerings", ["semester_id"])
    op.create_index("ix_course_offerings_section_id", "course_offerings", ["section_id"])

    # 10. Student Academic Profiles
    op.create_table(
        "student_academic_profiles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("program_id", sa.String(length=36), sa.ForeignKey("programs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("batch_id", sa.String(length=36), sa.ForeignKey("batches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("current_section_id", sa.String(length=36), sa.ForeignKey("sections.id", ondelete="SET NULL"), nullable=True),
        sa.Column("enrollment_number", sa.String(length=50), nullable=False),
        sa.Column("admission_year", sa.Integer(), nullable=False),
        sa.Column("graduation_year", sa.Integer(), nullable=False),
        sa.Column("academic_status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", name="uq_student_academic_profile_user_id"),
        sa.UniqueConstraint("institution_id", "enrollment_number", name="uq_student_inst_enrollment"),
    )
    op.create_index("ix_student_academic_profiles_user_id", "student_academic_profiles", ["user_id"])
    op.create_index("ix_student_academic_profiles_institution_id", "student_academic_profiles", ["institution_id"])
    op.create_index("ix_student_academic_profiles_program_id", "student_academic_profiles", ["program_id"])
    op.create_index("ix_student_academic_profiles_batch_id", "student_academic_profiles", ["batch_id"])

    # 11. Teacher Academic Profiles
    op.create_table(
        "teacher_academic_profiles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("department_id", sa.String(length=36), sa.ForeignKey("departments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("designation", sa.String(length=100), nullable=False, server_default="Assistant Professor"),
        sa.Column("employee_id", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", name="uq_teacher_academic_profile_user_id"),
        sa.UniqueConstraint("institution_id", "employee_id", name="uq_teacher_inst_employee"),
    )
    op.create_index("ix_teacher_academic_profiles_user_id", "teacher_academic_profiles", ["user_id"])
    op.create_index("ix_teacher_academic_profiles_institution_id", "teacher_academic_profiles", ["institution_id"])
    op.create_index("ix_teacher_academic_profiles_department_id", "teacher_academic_profiles", ["department_id"])

    # 12. Student Enrollments
    op.create_table(
        "student_enrollments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_profile_id", sa.String(length=36), sa.ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_offering_id", sa.String(length=36), sa.ForeignKey("course_offerings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("enrollment_status", sa.String(length=20), nullable=False, server_default="enrolled"),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("student_profile_id", "course_offering_id", name="uq_student_offering_enrollment"),
    )
    op.create_index("ix_student_enrollments_student_profile_id", "student_enrollments", ["student_profile_id"])
    op.create_index("ix_student_enrollments_course_offering_id", "student_enrollments", ["course_offering_id"])

    # 13. Teaching Assignments
    op.create_table(
        "teaching_assignments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("teacher_profile_id", sa.String(length=36), sa.ForeignKey("teacher_academic_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_offering_id", sa.String(length=36), sa.ForeignKey("course_offerings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assignment_role", sa.String(length=50), nullable=False, server_default="lead_instructor"),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.UniqueConstraint("teacher_profile_id", "course_offering_id", "assignment_role", name="uq_teacher_offering_role"),
    )
    op.create_index("ix_teaching_assignments_teacher_profile_id", "teaching_assignments", ["teacher_profile_id"])
    op.create_index("ix_teaching_assignments_course_offering_id", "teaching_assignments", ["course_offering_id"])


def downgrade() -> None:
    op.drop_table("teaching_assignments")
    op.drop_table("student_enrollments")
    op.drop_table("teacher_academic_profiles")
    op.drop_table("student_academic_profiles")
    op.drop_table("course_offerings")
    op.drop_table("courses")
    op.drop_table("sections")
    op.drop_table("batches")
    op.drop_table("semesters")
    op.drop_table("academic_years")
    op.drop_table("programs")
    op.drop_table("departments")
    op.drop_table("institutions")
