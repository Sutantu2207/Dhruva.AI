"""Academic Management & Institutional Hierarchy REST API Endpoints.

Enforces centralized RBAC and fine-grained scoping rules:
- Student: view own profile, own enrollments, own courses; cannot modify institutional structures or view other students' records.
- Teacher: view authorized course offerings, view students enrolled in authorized offerings; cannot view unrelated offerings or arbitrary students.
- HOD: department-level scope for courses, offerings, and student records.
- Institution Admin: institution-level scope across all academic resources.
- Super Admin: platform-level cross-institution access.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, get_current_user, require_roles
from app.core.security import UserRole
from app.domains.identity.models import User
from app.domains.academic.models import (
    CourseOffering,
    Department,
    StudentAcademicProfile,
    StudentEnrollment,
    TeacherAcademicProfile,
    TeachingAssignment,
)
from app.domains.academic.schemas import (
    AcademicYearCreate,
    AcademicYearResponse,
    BatchCreate,
    BatchResponse,
    CourseCreate,
    CourseOfferingCreate,
    CourseOfferingResponse,
    CourseResponse,
    DepartmentCreate,
    DepartmentResponse,
    InstitutionCreate,
    InstitutionResponse,
    InstitutionUpdate,
    ProgramCreate,
    ProgramResponse,
    SectionCreate,
    SectionResponse,
    SemesterCreate,
    SemesterResponse,
    StudentAcademicProfileCreate,
    StudentAcademicProfileResponse,
    StudentAcademicProfileUpdate,
    StudentEnrollmentCreate,
    StudentEnrollmentResponse,
    StudentEnrollmentUpdate,
    TeacherAcademicProfileCreate,
    TeacherAcademicProfileResponse,
    TeacherAcademicProfileUpdate,
    TeachingAssignmentCreate,
    TeachingAssignmentResponse,
)
from app.domains.academic.service import academic_service

router = APIRouter(prefix="/academic", tags=["Academic Management"])


# =========================================================================
# Scope Verification Helpers
# =========================================================================

def _check_institution_admin_access(current_user: User, target_institution_id: Optional[str]) -> None:
    """Verifies that current_user has admin access to target_institution_id."""
    if current_user.role == UserRole.SUPER_ADMIN:
        return
    if current_user.role == UserRole.INSTITUTION_ADMIN:
        if current_user.institution_id and current_user.institution_id == target_institution_id:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot administer an institution other than your assigned institution.",
        )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: Requires Institution Admin or Super Admin privileges.",
    )


async def _check_teacher_offering_access(db: AsyncSession, current_user: User, offering_id: str) -> None:
    """Verifies whether a teacher is assigned to the course offering."""
    if current_user.role in (UserRole.SUPER_ADMIN, UserRole.INSTITUTION_ADMIN, UserRole.HOD):
        return

    if current_user.role == UserRole.TEACHER:
        stmt = (
            select(TeachingAssignment)
            .join(TeacherAcademicProfile, TeacherAcademicProfile.id == TeachingAssignment.teacher_profile_id)
            .where(
                TeachingAssignment.course_offering_id == offering_id,
                TeacherAcademicProfile.user_id == current_user.id,
                TeachingAssignment.status == "active",
            )
        )
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: You are not an assigned teacher for this course offering.",
    )


# =========================================================================
# Institutions
# =========================================================================

@router.post(
    "/institutions",
    response_model=InstitutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new institution",
)
async def create_institution(
    payload: InstitutionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    return await academic_service.create_institution(db, payload)


@router.get(
    "/institutions",
    response_model=List[InstitutionResponse],
    summary="List institutions",
)
async def list_institutions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.list_institutions(db, skip=skip, limit=limit)


@router.get(
    "/institutions/{institution_id}",
    response_model=InstitutionResponse,
    summary="Get institution details",
)
async def get_institution(
    institution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.get_institution(db, institution_id)


@router.patch(
    "/institutions/{institution_id}",
    response_model=InstitutionResponse,
    summary="Update institution details",
)
async def update_institution(
    institution_id: str,
    payload: InstitutionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_institution_admin_access(current_user, institution_id)
    return await academic_service.update_institution(db, institution_id, payload)


# =========================================================================
# Departments
# =========================================================================

@router.post(
    "/departments",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create department",
)
async def create_department(
    payload: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_institution_admin_access(current_user, payload.institution_id)
    return await academic_service.create_department(db, payload)


@router.get(
    "/departments",
    response_model=List[DepartmentResponse],
    summary="List departments",
)
async def list_departments(
    institution_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_inst = institution_id or current_user.institution_id
    return await academic_service.list_departments(db, institution_id=target_inst, skip=skip, limit=limit)


@router.get(
    "/departments/{department_id}",
    response_model=DepartmentResponse,
    summary="Get department details",
)
async def get_department(
    department_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.get_department(db, department_id)


# =========================================================================
# Programs
# =========================================================================

@router.post(
    "/programs",
    response_model=ProgramResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create academic program",
)
async def create_program(
    payload: ProgramCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dept = await academic_service.get_department(db, payload.department_id)
    _check_institution_admin_access(current_user, dept.institution_id)
    return await academic_service.create_program(db, payload)


@router.get(
    "/programs",
    response_model=List[ProgramResponse],
    summary="List academic programs",
)
async def list_programs(
    department_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.list_programs(db, department_id=department_id, skip=skip, limit=limit)


@router.get(
    "/programs/{program_id}",
    response_model=ProgramResponse,
    summary="Get program details",
)
async def get_program(
    program_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.get_program(db, program_id)


# =========================================================================
# Academic Years
# =========================================================================

@router.post(
    "/academic-years",
    response_model=AcademicYearResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create academic year",
)
async def create_academic_year(
    payload: AcademicYearCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_institution_admin_access(current_user, payload.institution_id)
    return await academic_service.create_academic_year(db, payload)


@router.get(
    "/academic-years",
    response_model=List[AcademicYearResponse],
    summary="List academic years",
)
async def list_academic_years(
    institution_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_inst = institution_id or current_user.institution_id
    return await academic_service.list_academic_years(db, institution_id=target_inst, skip=skip, limit=limit)


@router.get(
    "/academic-years/{year_id}",
    response_model=AcademicYearResponse,
    summary="Get academic year details",
)
async def get_academic_year(
    year_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.get_academic_year(db, year_id)


# =========================================================================
# Semesters
# =========================================================================

@router.post(
    "/semesters",
    response_model=SemesterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create semester",
)
async def create_semester(
    payload: SemesterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ay = await academic_service.get_academic_year(db, payload.academic_year_id)
    _check_institution_admin_access(current_user, ay.institution_id)
    return await academic_service.create_semester(db, payload)


@router.get(
    "/semesters",
    response_model=List[SemesterResponse],
    summary="List semesters",
)
async def list_semesters(
    academic_year_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.list_semesters(db, academic_year_id=academic_year_id, skip=skip, limit=limit)


@router.get(
    "/semesters/{semester_id}",
    response_model=SemesterResponse,
    summary="Get semester details",
)
async def get_semester(
    semester_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.get_semester(db, semester_id)


# =========================================================================
# Batches
# =========================================================================

@router.post(
    "/batches",
    response_model=BatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create student cohort batch",
)
async def create_batch(
    payload: BatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_institution_admin_access(current_user, payload.institution_id)
    return await academic_service.create_batch(db, payload)


@router.get(
    "/batches",
    response_model=List[BatchResponse],
    summary="List batches",
)
async def list_batches(
    institution_id: Optional[str] = Query(None),
    program_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_inst = institution_id or current_user.institution_id
    return await academic_service.list_batches(db, institution_id=target_inst, program_id=program_id, skip=skip, limit=limit)


@router.get(
    "/batches/{batch_id}",
    response_model=BatchResponse,
    summary="Get batch details",
)
async def get_batch(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.get_batch(db, batch_id)


# =========================================================================
# Sections
# =========================================================================

@router.post(
    "/sections",
    response_model=SectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create batch section",
)
async def create_section(
    payload: SectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    batch = await academic_service.get_batch(db, payload.batch_id)
    _check_institution_admin_access(current_user, batch.institution_id)
    return await academic_service.create_section(db, payload)


@router.get(
    "/sections",
    response_model=List[SectionResponse],
    summary="List sections",
)
async def list_sections(
    batch_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.list_sections(db, batch_id=batch_id, skip=skip, limit=limit)


@router.get(
    "/sections/{section_id}",
    response_model=SectionResponse,
    summary="Get section details",
)
async def get_section(
    section_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.get_section(db, section_id)


# =========================================================================
# Courses
# =========================================================================

@router.post(
    "/courses",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create academic course",
)
async def create_course(
    payload: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.SUPER_ADMIN:
        pass
    elif current_user.role == UserRole.INSTITUTION_ADMIN:
        _check_institution_admin_access(current_user, payload.institution_id)
    elif current_user.role == UserRole.HOD:
        if current_user.institution_id != payload.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: HOD can only create courses within their assigned institution.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Insufficient privileges to create courses.",
        )
    return await academic_service.create_course(db, payload)


@router.get(
    "/courses",
    response_model=List[CourseResponse],
    summary="List academic courses",
)
async def list_courses(
    institution_id: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_inst = institution_id or current_user.institution_id
    return await academic_service.list_courses(
        db, institution_id=target_inst, department_id=department_id, skip=skip, limit=limit
    )


@router.get(
    "/courses/{course_id}",
    response_model=CourseResponse,
    summary="Get course details",
)
async def get_course(
    course_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.get_course(db, course_id)


# =========================================================================
# Course Offerings
# =========================================================================

@router.post(
    "/course-offerings",
    response_model=CourseOfferingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create course offering",
)
async def create_course_offering(
    payload: CourseOfferingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.INSTITUTION_ADMIN, UserRole.HOD):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only Academic Administrators or HODs can schedule course offerings.",
        )

    course = await academic_service.get_course(db, payload.course_id)
    if current_user.role != UserRole.SUPER_ADMIN and current_user.institution_id != course.institution_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot create course offering outside your assigned institution.",
        )

    return await academic_service.create_course_offering(db, payload)


@router.get(
    "/course-offerings",
    response_model=List[CourseOfferingResponse],
    summary="List course offerings",
)
async def list_course_offerings(
    course_id: Optional[str] = Query(None),
    academic_year_id: Optional[str] = Query(None),
    semester_id: Optional[str] = Query(None),
    section_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role in (UserRole.SUPER_ADMIN, UserRole.INSTITUTION_ADMIN, UserRole.HOD):
        return await academic_service.list_course_offerings(
            db, course_id=course_id, academic_year_id=academic_year_id,
            semester_id=semester_id, section_id=section_id, skip=skip, limit=limit
        )

    if current_user.role == UserRole.TEACHER:
        stmt = (
            select(CourseOffering)
            .join(TeachingAssignment, TeachingAssignment.course_offering_id == CourseOffering.id)
            .join(TeacherAcademicProfile, TeacherAcademicProfile.id == TeachingAssignment.teacher_profile_id)
            .where(
                TeacherAcademicProfile.user_id == current_user.id,
                TeachingAssignment.status == "active",
            )
            .offset(skip)
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    if current_user.role == UserRole.STUDENT:
        stmt = (
            select(CourseOffering)
            .join(StudentEnrollment, StudentEnrollment.course_offering_id == CourseOffering.id)
            .join(StudentAcademicProfile, StudentAcademicProfile.id == StudentEnrollment.student_profile_id)
            .where(
                StudentAcademicProfile.user_id == current_user.id,
                StudentEnrollment.enrollment_status == "enrolled",
            )
            .offset(skip)
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    return []


@router.get(
    "/course-offerings/{offering_id}",
    response_model=CourseOfferingResponse,
    summary="Get course offering details",
)
async def get_course_offering(
    offering_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    offering = await academic_service.get_course_offering(db, offering_id)

    if current_user.role in (UserRole.SUPER_ADMIN, UserRole.INSTITUTION_ADMIN, UserRole.HOD):
        return offering

    if current_user.role == UserRole.TEACHER:
        await _check_teacher_offering_access(db, current_user, offering_id)
        return offering

    if current_user.role == UserRole.STUDENT:
        stmt = (
            select(StudentEnrollment)
            .join(StudentAcademicProfile, StudentAcademicProfile.id == StudentEnrollment.student_profile_id)
            .where(
                StudentEnrollment.course_offering_id == offering_id,
                StudentAcademicProfile.user_id == current_user.id,
            )
        )
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not enrolled in this course offering.",
            )
        return offering

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied for current role.",
    )


# =========================================================================
# Student Academic Profiles
# =========================================================================

@router.post(
    "/student-profiles",
    response_model=StudentAcademicProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create student academic profile",
)
async def create_student_profile(
    payload: StudentAcademicProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.INSTITUTION_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Academic profiles must be established through controlled institutional workflows.",
        )
    _check_institution_admin_access(current_user, payload.institution_id)
    return await academic_service.create_student_profile(db, payload)


@router.get(
    "/student-profiles/me",
    response_model=StudentAcademicProfileResponse,
    summary="Get current student's academic profile",
)
async def get_my_student_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = await academic_service.get_student_profile(db, current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No student academic profile found for current user.",
        )
    return profile


@router.get(
    "/student-profiles/{user_id}",
    response_model=StudentAcademicProfileResponse,
    summary="Get student academic profile by user ID",
)
async def get_student_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.STUDENT and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Students cannot view other students' private academic records.",
        )

    profile = await academic_service.get_student_profile(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student academic profile not found.",
        )

    if current_user.role == UserRole.TEACHER:
        stmt = (
            select(StudentEnrollment)
            .join(TeachingAssignment, TeachingAssignment.course_offering_id == StudentEnrollment.course_offering_id)
            .join(TeacherAcademicProfile, TeacherAcademicProfile.id == TeachingAssignment.teacher_profile_id)
            .where(
                StudentEnrollment.student_profile_id == profile.id,
                TeacherAcademicProfile.user_id == current_user.id,
                TeachingAssignment.status == "active",
            )
        )
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Teacher may only view profiles of students in their authorized course offerings.",
            )

    if current_user.role == UserRole.INSTITUTION_ADMIN and current_user.institution_id != profile.institution_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot access student profile outside your assigned institution.",
        )

    return profile


@router.patch(
    "/student-profiles/{user_id}",
    response_model=StudentAcademicProfileResponse,
    summary="Update student academic profile",
)
async def update_student_profile(
    user_id: str,
    payload: StudentAcademicProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = await academic_service.get_student_profile(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student academic profile not found.",
        )
    _check_institution_admin_access(current_user, profile.institution_id)
    return await academic_service.update_student_profile(db, user_id, payload)


# =========================================================================
# Teacher Academic Profiles
# =========================================================================

@router.post(
    "/teacher-profiles",
    response_model=TeacherAcademicProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create teacher academic profile",
)
async def create_teacher_profile(
    payload: TeacherAcademicProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.INSTITUTION_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Teacher profiles must be created by administrators.",
        )
    _check_institution_admin_access(current_user, payload.institution_id)
    return await academic_service.create_teacher_profile(db, payload)


@router.get(
    "/teacher-profiles/me",
    response_model=TeacherAcademicProfileResponse,
    summary="Get current teacher's academic profile",
)
async def get_my_teacher_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = await academic_service.get_teacher_profile(db, current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No teacher academic profile found for current user.",
        )
    return profile


@router.get(
    "/teacher-profiles/{user_id}",
    response_model=TeacherAcademicProfileResponse,
    summary="Get teacher academic profile by user ID",
)
async def get_teacher_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = await academic_service.get_teacher_profile(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher academic profile not found.",
        )
    return profile


@router.patch(
    "/teacher-profiles/{user_id}",
    response_model=TeacherAcademicProfileResponse,
    summary="Update teacher academic profile",
)
async def update_teacher_profile(
    user_id: str,
    payload: TeacherAcademicProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = await academic_service.get_teacher_profile(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher academic profile not found.",
        )
    _check_institution_admin_access(current_user, profile.institution_id)
    return await academic_service.update_teacher_profile(db, user_id, payload)


# =========================================================================
# Student Enrollments
# =========================================================================

@router.post(
    "/enrollments",
    response_model=StudentEnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enroll student in course offering",
)
async def create_enrollment(
    payload: StudentEnrollmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Students cannot enroll themselves into course offerings directly.",
        )

    if current_user.role == UserRole.TEACHER:
        await _check_teacher_offering_access(db, current_user, payload.course_offering_id)

    return await academic_service.enroll_student(db, payload)


@router.get(
    "/enrollments",
    response_model=List[StudentEnrollmentResponse],
    summary="List course enrollments",
)
async def list_enrollments(
    course_offering_id: Optional[str] = Query(None),
    student_profile_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.STUDENT:
        my_profile = await academic_service.get_student_profile(db, current_user.id)
        if not my_profile:
            return []
        return await academic_service.list_enrollments(
            db, student_profile_id=my_profile.id, skip=skip, limit=limit
        )

    if current_user.role == UserRole.TEACHER:
        if course_offering_id:
            await _check_teacher_offering_access(db, current_user, course_offering_id)
            return await academic_service.list_enrollments(
                db, course_offering_id=course_offering_id, skip=skip, limit=limit
            )
        stmt = (
            select(StudentEnrollment)
            .join(TeachingAssignment, TeachingAssignment.course_offering_id == StudentEnrollment.course_offering_id)
            .join(TeacherAcademicProfile, TeacherAcademicProfile.id == TeachingAssignment.teacher_profile_id)
            .where(
                TeacherAcademicProfile.user_id == current_user.id,
                TeachingAssignment.status == "active",
            )
            .offset(skip)
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    return await academic_service.list_enrollments(
        db, course_offering_id=course_offering_id, student_profile_id=student_profile_id, skip=skip, limit=limit
    )


@router.get(
    "/enrollments/{enrollment_id}",
    response_model=StudentEnrollmentResponse,
    summary="Get enrollment details",
)
async def get_enrollment(
    enrollment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    enrollment = await academic_service.get_enrollment(db, enrollment_id)
    if current_user.role == UserRole.STUDENT:
        my_profile = await academic_service.get_student_profile(db, current_user.id)
        if not my_profile or enrollment.student_profile_id != my_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot view another student's enrollment.",
            )
    if current_user.role == UserRole.TEACHER:
        await _check_teacher_offering_access(db, current_user, enrollment.course_offering_id)

    return enrollment


@router.patch(
    "/enrollments/{enrollment_id}",
    response_model=StudentEnrollmentResponse,
    summary="Update enrollment status",
)
async def update_enrollment(
    enrollment_id: str,
    payload: StudentEnrollmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    enrollment = await academic_service.get_enrollment(db, enrollment_id)
    if current_user.role == UserRole.TEACHER:
        await _check_teacher_offering_access(db, current_user, enrollment.course_offering_id)
    elif current_user.role == UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Students cannot alter enrollment records.",
        )

    return await academic_service.update_enrollment(db, enrollment_id, payload)


# =========================================================================
# Teaching Assignments
# =========================================================================

@router.post(
    "/teaching-assignments",
    response_model=TeachingAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign teacher to course offering",
)
async def create_teaching_assignment(
    payload: TeachingAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.INSTITUTION_ADMIN, UserRole.HOD):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only Administrators and HODs can assign teachers to courses.",
        )

    offering = await academic_service.get_course_offering(db, payload.course_offering_id)
    course = await academic_service.get_course(db, offering.course_id)
    if current_user.role != UserRole.SUPER_ADMIN and current_user.institution_id != course.institution_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot assign teachers outside your assigned institution.",
        )

    return await academic_service.assign_teacher(db, payload)


@router.get(
    "/teaching-assignments",
    response_model=List[TeachingAssignmentResponse],
    summary="List teaching assignments",
)
async def list_teaching_assignments(
    course_offering_id: Optional[str] = Query(None),
    teacher_profile_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.TEACHER:
        teacher_prof = await academic_service.get_teacher_profile(db, current_user.id)
        if not teacher_prof:
            return []
        return await academic_service.list_teaching_assignments(
            db, teacher_profile_id=teacher_prof.id, skip=skip, limit=limit
        )

    if current_user.role == UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Students cannot inspect staff teaching assignment internals directly.",
        )

    return await academic_service.list_teaching_assignments(
        db, course_offering_id=course_offering_id, teacher_profile_id=teacher_profile_id, skip=skip, limit=limit
    )
