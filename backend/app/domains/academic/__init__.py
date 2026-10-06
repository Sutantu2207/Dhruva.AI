"""
Dhruva.AI - Academic Management & Institutional Hierarchy Domain
"""

from app.domains.academic.models import (
    Institution,
    Department,
    Program,
    AcademicYear,
    Semester,
    Batch,
    Section,
    Course,
    CourseOffering,
    StudentAcademicProfile,
    TeacherAcademicProfile,
    StudentEnrollment,
    TeachingAssignment,
)
from app.domains.academic.service import academic_service

__all__ = [
    "Institution",
    "Department",
    "Program",
    "AcademicYear",
    "Semester",
    "Batch",
    "Section",
    "Course",
    "CourseOffering",
    "StudentAcademicProfile",
    "TeacherAcademicProfile",
    "StudentEnrollment",
    "TeachingAssignment",
    "academic_service",
]
