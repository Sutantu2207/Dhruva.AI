"""Database models for Academic Management & Institutional Hierarchy domain."""

import uuid
from datetime import datetime, timezone, date
from typing import List, Optional
from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    Date,
    Integer,
    Float,
    ForeignKey,
    UniqueConstraint,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Institution(Base):
    """Institutional top-level entity representing a university, college, or campus."""
    __tablename__ = "institutions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email_domains: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # e.g. "college.edu,eng.edu"
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    departments: Mapped[List["Department"]] = relationship("Department", back_populates="institution", cascade="all, delete-orphan")
    academic_years: Mapped[List["AcademicYear"]] = relationship("AcademicYear", back_populates="institution", cascade="all, delete-orphan")
    courses: Mapped[List["Course"]] = relationship("Course", back_populates="institution", cascade="all, delete-orphan")


class Department(Base):
    """Academic department belonging to an institution (e.g., Computer Science, Mechanical)."""
    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint("institution_id", "code", name="uq_department_inst_code"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    institution: Mapped["Institution"] = relationship("Institution", back_populates="departments")
    programs: Mapped[List["Program"]] = relationship("Program", back_populates="department", cascade="all, delete-orphan")
    courses: Mapped[List["Course"]] = relationship("Course", back_populates="department", cascade="all, delete-orphan")


class Program(Base):
    """Degree program belonging to a department (e.g. B.Tech Computer Science, M.Tech AI)."""
    __tablename__ = "programs"
    __table_args__ = (
        UniqueConstraint("department_id", "code", name="uq_program_dept_code"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    department_id: Mapped[str] = mapped_column(String(36), ForeignKey("departments.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    degree_type: Mapped[str] = mapped_column(String(50), nullable=False)  # B.Tech, B.E., M.Tech, Ph.D.
    duration_years: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    department: Mapped["Department"] = relationship("Department", back_populates="programs")
    batches: Mapped[List["Batch"]] = relationship("Batch", back_populates="program", cascade="all, delete-orphan")


class AcademicYear(Base):
    """Academic calendar period (e.g., 2026-27)."""
    __tablename__ = "academic_years"
    __table_args__ = (
        UniqueConstraint("institution_id", "name", name="uq_academic_year_inst_name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # "2026-27"
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    institution: Mapped["Institution"] = relationship("Institution", back_populates="academic_years")
    semesters: Mapped[List["Semester"]] = relationship("Semester", back_populates="academic_year", cascade="all, delete-orphan")


class Semester(Base):
    """Semester within an academic year."""
    __tablename__ = "semesters"
    __table_args__ = (
        UniqueConstraint("academic_year_id", "semester_number", name="uq_semester_year_num"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    academic_year_id: Mapped[str] = mapped_column(String(36), ForeignKey("academic_years.id", ondelete="CASCADE"), index=True, nullable=False)
    semester_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 to 10
    label: Mapped[str] = mapped_column(String(50), nullable=False)  # "Semester 1", "Odd 2026"
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    academic_year: Mapped["AcademicYear"] = relationship("AcademicYear", back_populates="semesters")


class Batch(Base):
    """Student cohort admitted in a specific year (e.g., 2023-2027)."""
    __tablename__ = "batches"
    __table_args__ = (
        UniqueConstraint("program_id", "label", name="uq_batch_prog_label"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=False)
    program_id: Mapped[str] = mapped_column(String(36), ForeignKey("programs.id", ondelete="CASCADE"), index=True, nullable=False)
    admission_year: Mapped[int] = mapped_column(Integer, nullable=False)
    graduation_year: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(50), nullable=False)  # "2023-2027"
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    program: Mapped["Program"] = relationship("Program", back_populates="batches")
    sections: Mapped[List["Section"]] = relationship("Section", back_populates="batch", cascade="all, delete-orphan")


class Section(Base):
    """Class section within a batch (e.g., Section A, Section B)."""
    __tablename__ = "sections"
    __table_args__ = (
        UniqueConstraint("batch_id", "name", name="uq_section_batch_name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id: Mapped[str] = mapped_column(String(36), ForeignKey("batches.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # "A", "B", "CSE-1"
    capacity: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    batch: Mapped["Batch"] = relationship("Batch", back_populates="sections")


class Course(Base):
    """Abstract curriculum course/subject definition."""
    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint("institution_id", "code", name="uq_course_inst_code"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=False)
    department_id: Mapped[str] = mapped_column(String(36), ForeignKey("departments.id", ondelete="CASCADE"), index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)  # "CS101"
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    credits: Mapped[float] = mapped_column(Float, default=3.0, nullable=False)
    course_type: Mapped[str] = mapped_column(String(50), default="core", nullable=False)  # core, elective, lab, project
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    institution: Mapped["Institution"] = relationship("Institution", back_populates="courses")
    department: Mapped["Department"] = relationship("Department", back_populates="courses")
    offerings: Mapped[List["CourseOffering"]] = relationship("CourseOffering", back_populates="course", cascade="all, delete-orphan")


class CourseOffering(Base):
    """Delivery of a course to a specific section during an academic year and semester."""
    __tablename__ = "course_offerings"
    __table_args__ = (
        UniqueConstraint("course_id", "academic_year_id", "semester_id", "section_id", name="uq_offering_period_section"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False)
    academic_year_id: Mapped[str] = mapped_column(String(36), ForeignKey("academic_years.id", ondelete="CASCADE"), index=True, nullable=False)
    semester_id: Mapped[str] = mapped_column(String(36), ForeignKey("semesters.id", ondelete="CASCADE"), index=True, nullable=False)
    section_id: Mapped[str] = mapped_column(String(36), ForeignKey("sections.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # active, completed, archived
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    course: Mapped["Course"] = relationship("Course", back_populates="offerings")
    section: Mapped["Section"] = relationship("Section")
    semester: Mapped["Semester"] = relationship("Semester")
    academic_year: Mapped["AcademicYear"] = relationship("AcademicYear")
    enrollments: Mapped[List["StudentEnrollment"]] = relationship("StudentEnrollment", back_populates="offering", cascade="all, delete-orphan")
    teaching_assignments: Mapped[List["TeachingAssignment"]] = relationship("TeachingAssignment", back_populates="offering", cascade="all, delete-orphan")


class StudentAcademicProfile(Base):
    """Academic membership and cohort tracking for an authenticated student user."""
    __tablename__ = "student_academic_profiles"
    __table_args__ = (
        UniqueConstraint("institution_id", "enrollment_number", name="uq_student_inst_enrollment"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=False)
    program_id: Mapped[str] = mapped_column(String(36), ForeignKey("programs.id", ondelete="CASCADE"), index=True, nullable=False)
    batch_id: Mapped[str] = mapped_column(String(36), ForeignKey("batches.id", ondelete="CASCADE"), index=True, nullable=False)
    current_section_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("sections.id", ondelete="SET NULL"), nullable=True)
    enrollment_number: Mapped[str] = mapped_column(String(50), nullable=False)  # Roll number / USN / Reg ID
    admission_year: Mapped[int] = mapped_column(Integer, nullable=False)
    graduation_year: Mapped[int] = mapped_column(Integer, nullable=False)
    academic_status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # active, graduated, suspended, withdrawn
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    institution: Mapped["Institution"] = relationship("Institution")
    program: Mapped["Program"] = relationship("Program")
    batch: Mapped["Batch"] = relationship("Batch")
    current_section: Mapped[Optional["Section"]] = relationship("Section")
    enrollments: Mapped[List["StudentEnrollment"]] = relationship("StudentEnrollment", back_populates="student_profile", cascade="all, delete-orphan")


class TeacherAcademicProfile(Base):
    """Academic profile and departmental affiliation for an authenticated teacher/faculty user."""
    __tablename__ = "teacher_academic_profiles"
    __table_args__ = (
        UniqueConstraint("institution_id", "employee_id", name="uq_teacher_inst_employee"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=False)
    department_id: Mapped[str] = mapped_column(String(36), ForeignKey("departments.id", ondelete="CASCADE"), index=True, nullable=False)
    designation: Mapped[str] = mapped_column(String(100), default="Assistant Professor", nullable=False)
    employee_id: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # active, on_leave, resigned
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    institution: Mapped["Institution"] = relationship("Institution")
    department: Mapped["Department"] = relationship("Department")
    teaching_assignments: Mapped[List["TeachingAssignment"]] = relationship("TeachingAssignment", back_populates="teacher_profile", cascade="all, delete-orphan")


class StudentEnrollment(Base):
    """Enrollment relationship between a student and a specific course offering."""
    __tablename__ = "student_enrollments"
    __table_args__ = (
        UniqueConstraint("student_profile_id", "course_offering_id", name="uq_student_offering_enrollment"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    course_offering_id: Mapped[str] = mapped_column(String(36), ForeignKey("course_offerings.id", ondelete="CASCADE"), index=True, nullable=False)
    enrollment_status: Mapped[str] = mapped_column(String(20), default="enrolled", nullable=False)  # enrolled, dropped, completed, audit
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    student_profile: Mapped["StudentAcademicProfile"] = relationship("StudentAcademicProfile", back_populates="enrollments")
    offering: Mapped["CourseOffering"] = relationship("CourseOffering", back_populates="enrollments")


class TeachingAssignment(Base):
    """Teaching assignment connecting faculty to a specific course offering."""
    __tablename__ = "teaching_assignments"
    __table_args__ = (
        UniqueConstraint("teacher_profile_id", "course_offering_id", "assignment_role", name="uq_teacher_offering_role"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    teacher_profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("teacher_academic_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    course_offering_id: Mapped[str] = mapped_column(String(36), ForeignKey("course_offerings.id", ondelete="CASCADE"), index=True, nullable=False)
    assignment_role: Mapped[str] = mapped_column(String(50), default="lead_instructor", nullable=False)  # lead_instructor, co_instructor, lab_instructor
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)

    teacher_profile: Mapped["TeacherAcademicProfile"] = relationship("TeacherAcademicProfile", back_populates="teaching_assignments")
    offering: Mapped["CourseOffering"] = relationship("CourseOffering", back_populates="teaching_assignments")
