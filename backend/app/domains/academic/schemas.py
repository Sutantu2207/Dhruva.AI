"""Pydantic schemas for Academic Management and Institutional Hierarchy."""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ---------------- Institutions ----------------
class InstitutionCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    code: str = Field(min_length=2, max_length=50)
    email_domains: Optional[str] = None


class InstitutionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    email_domains: Optional[str] = None
    status: Optional[str] = None


class InstitutionResponse(InstitutionCreate):
    id: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------- Departments ----------------
class DepartmentCreate(BaseModel):
    institution_id: str
    name: str = Field(min_length=2, max_length=255)
    code: str = Field(min_length=2, max_length=50)


class DepartmentResponse(DepartmentCreate):
    id: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------- Programs ----------------
class ProgramCreate(BaseModel):
    department_id: str
    name: str = Field(min_length=2, max_length=255)
    code: str = Field(min_length=2, max_length=50)
    degree_type: str = Field(default="B.Tech")
    duration_years: int = Field(default=4, ge=1, le=6)


class ProgramResponse(ProgramCreate):
    id: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------- Academic Years ----------------
class AcademicYearCreate(BaseModel):
    institution_id: str
    name: str = Field(min_length=4, max_length=50)  # e.g., "2026-27"
    start_date: date
    end_date: date


class AcademicYearResponse(AcademicYearCreate):
    id: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------- Semesters ----------------
class SemesterCreate(BaseModel):
    academic_year_id: str
    semester_number: int = Field(ge=1, le=12)
    label: str = Field(min_length=1, max_length=50)
    start_date: date
    end_date: date


class SemesterResponse(SemesterCreate):
    id: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------- Batches ----------------
class BatchCreate(BaseModel):
    institution_id: str
    program_id: str
    admission_year: int = Field(ge=2000, le=2100)
    graduation_year: int = Field(ge=2000, le=2100)
    label: str = Field(min_length=4, max_length=50)


class BatchResponse(BatchCreate):
    id: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------- Sections ----------------
class SectionCreate(BaseModel):
    batch_id: str
    name: str = Field(min_length=1, max_length=50)
    capacity: int = Field(default=60, ge=1, le=300)


class SectionResponse(SectionCreate):
    id: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------- Courses ----------------
class CourseCreate(BaseModel):
    institution_id: str
    department_id: str
    code: str = Field(min_length=2, max_length=50)
    title: str = Field(min_length=2, max_length=255)
    description: Optional[str] = None
    credits: float = Field(default=3.0, ge=0.5, le=30.0)
    course_type: str = Field(default="core")


class CourseResponse(CourseCreate):
    id: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------- Course Offerings ----------------
class CourseOfferingCreate(BaseModel):
    course_id: str
    academic_year_id: str
    semester_id: str
    section_id: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class CourseOfferingResponse(CourseOfferingCreate):
    id: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------- Student Academic Profiles ----------------
class StudentAcademicProfileCreate(BaseModel):
    user_id: str
    institution_id: str
    program_id: str
    batch_id: str
    current_section_id: Optional[str] = None
    enrollment_number: str = Field(min_length=2, max_length=50)
    admission_year: int
    graduation_year: int


class StudentAcademicProfileUpdate(BaseModel):
    current_section_id: Optional[str] = None
    academic_status: Optional[str] = None
    graduation_year: Optional[int] = None


class StudentAcademicProfileResponse(StudentAcademicProfileCreate):
    id: str
    academic_status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------- Teacher Academic Profiles ----------------
class TeacherAcademicProfileCreate(BaseModel):
    user_id: str
    institution_id: str
    department_id: str
    designation: str = "Assistant Professor"
    employee_id: str = Field(min_length=2, max_length=50)


class TeacherAcademicProfileUpdate(BaseModel):
    designation: Optional[str] = None
    status: Optional[str] = None


class TeacherAcademicProfileResponse(TeacherAcademicProfileCreate):
    id: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------- Student Enrollments ----------------
class StudentEnrollmentCreate(BaseModel):
    student_profile_id: str
    course_offering_id: str
    enrollment_status: str = "enrolled"


class StudentEnrollmentUpdate(BaseModel):
    enrollment_status: str


class StudentEnrollmentResponse(StudentEnrollmentCreate):
    id: str
    enrolled_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------- Teaching Assignments ----------------
class TeachingAssignmentCreate(BaseModel):
    teacher_profile_id: str
    course_offering_id: str
    assignment_role: str = "lead_instructor"


class TeachingAssignmentResponse(TeachingAssignmentCreate):
    id: str
    assigned_at: datetime
    status: str
    model_config = ConfigDict(from_attributes=True)
