"""Comprehensive test suite for Domain 2: Academic Management & Institutional Hierarchy.

Validates:
1. Institution creation authorization (Super Admin only)
2. Department creation
3. Department institution relationship & uniqueness
4. Program relationship & uniqueness
5. Academic year creation & validation
6. Semester creation & uniqueness
7. Batch cohort creation & validation
8. Section creation & uniqueness
9. Course creation & uniqueness
10. Course offering scheduling & uniqueness
11. Student academic profile creation & linking
12. Teacher academic profile creation & linking
13. Student enrollment
14. Teaching assignment
15. Duplicate enrollment prevention
16. Duplicate teaching assignment prevention
17. Student cannot modify academic structure
18. Student cannot self-assign to institution/profile
19. Student cannot access another student's private profile
20. Teacher cannot access unrelated course offerings
21. Teacher can access authorized enrolled students
22. HOD department scoping
23. Institution admin institution scoping
24. Super admin cross-institution access
25. Foreign-key integrity
26. Invalid relationships rejected
"""

from datetime import date
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import UserRole, create_access_token, get_password_hash
from app.domains.identity.models import User
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


async def create_user_helper(
    db: AsyncSession,
    email: str,
    role: UserRole,
    first_name: str = "Test",
    last_name: str = "User",
    institution_id: str = None,
) -> tuple[User, str]:
    """Helper to persist a user in the test database and generate an auth token."""
    user = User(
        email=email,
        normalized_email=email.strip().lower(),
        hashed_password=get_password_hash("SecurePassword123!"),
        first_name=first_name,
        last_name=last_name,
        display_name=f"{first_name} {last_name}",
        role=role,
        institution_id=institution_id,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token(subject=user.id, role=user.role)
    return user, token


@pytest.mark.asyncio
async def test_01_institution_creation_authorization(async_client: AsyncClient, db_session: AsyncSession):
    """1. Super Admin can create institution; student or unauthenticated is rejected."""
    _, super_token = await create_user_helper(db_session, "super@dhruva.ai", UserRole.SUPER_ADMIN)
    _, student_token = await create_user_helper(db_session, "stu1@dhruva.ai", UserRole.STUDENT)

    payload = {"name": "National Institute of Technology", "code": "NIT01", "email_domains": "nit.edu"}

    # Unauthenticated -> 401
    unauth_res = await async_client.post("/api/v1/academic/institutions", json=payload)
    assert unauth_res.status_code == 401

    # Student -> 403 Forbidden
    stu_res = await async_client.post(
        "/api/v1/academic/institutions", json=payload, headers={"Authorization": f"Bearer {student_token}"}
    )
    assert stu_res.status_code == 403

    # Super Admin -> 201 Created
    super_res = await async_client.post(
        "/api/v1/academic/institutions", json=payload, headers={"Authorization": f"Bearer {super_token}"}
    )
    assert super_res.status_code == 201
    data = super_res.json()
    assert data["name"] == "National Institute of Technology"
    assert data["code"] == "NIT01"


@pytest.mark.asyncio
async def test_02_department_creation(async_client: AsyncClient, db_session: AsyncSession):
    """2. Department creation by Institution Admin."""
    inst = Institution(name="Apex Engineering College", code="APEX")
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)

    _, admin_token = await create_user_helper(
        db_session, "admin@apex.edu", UserRole.INSTITUTION_ADMIN, institution_id=inst.id
    )

    dept_payload = {"institution_id": inst.id, "name": "Computer Science & Engineering", "code": "CSE"}
    res = await async_client.post(
        "/api/v1/academic/departments", json=dept_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Computer Science & Engineering"
    assert data["code"] == "CSE"
    assert data["institution_id"] == inst.id


@pytest.mark.asyncio
async def test_03_department_institution_relationship(async_client: AsyncClient, db_session: AsyncSession):
    """3. Department institution relationship & duplicate code in same institution rejected."""
    inst = Institution(name="BMS College of Engineering", code="BMSCE")
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)

    _, admin_token = await create_user_helper(
        db_session, "admin@bmsce.edu", UserRole.INSTITUTION_ADMIN, institution_id=inst.id
    )

    dept_payload = {"institution_id": inst.id, "name": "Mechanical Engineering", "code": "MECH"}
    res1 = await async_client.post(
        "/api/v1/academic/departments", json=dept_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res1.status_code == 201

    # Duplicate code in same institution -> 409 Conflict
    res2 = await async_client.post(
        "/api/v1/academic/departments", json=dept_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res2.status_code == 409


@pytest.mark.asyncio
async def test_04_program_relationship(async_client: AsyncClient, db_session: AsyncSession):
    """4. Program belongs to department; duplicate program code in same department rejected."""
    inst = Institution(name="Global Institute", code="GI")
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)

    dept = Department(institution_id=inst.id, name="Information Technology", code="IT")
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)

    _, admin_token = await create_user_helper(
        db_session, "admin@gi.edu", UserRole.INSTITUTION_ADMIN, institution_id=inst.id
    )

    prog_payload = {
        "department_id": dept.id,
        "name": "B.Tech Information Technology",
        "code": "BTECH-IT",
        "degree_type": "B.Tech",
        "duration_years": 4,
    }
    res = await async_client.post(
        "/api/v1/academic/programs", json=prog_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 201
    assert res.json()["code"] == "BTECH-IT"

    # Duplicate program code in same department -> 409
    dup_res = await async_client.post(
        "/api/v1/academic/programs", json=prog_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert dup_res.status_code == 409


@pytest.mark.asyncio
async def test_05_academic_year(async_client: AsyncClient, db_session: AsyncSession):
    """5. Academic year creation & start_date < end_date validation."""
    inst = Institution(name="Tech Univ", code="TU")
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)

    _, admin_token = await create_user_helper(
        db_session, "admin@tu.edu", UserRole.INSTITUTION_ADMIN, institution_id=inst.id
    )

    # Valid academic year
    ay_payload = {
        "institution_id": inst.id,
        "name": "2026-27",
        "start_date": "2026-08-01",
        "end_date": "2027-05-31",
    }
    res = await async_client.post(
        "/api/v1/academic/academic-years", json=ay_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 201
    assert res.json()["name"] == "2026-27"

    # Duplicate name -> 409
    dup_res = await async_client.post(
        "/api/v1/academic/academic-years", json=ay_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert dup_res.status_code == 409

    # Invalid dates (start >= end) -> 400
    invalid_payload = {
        "institution_id": inst.id,
        "name": "2027-28",
        "start_date": "2027-08-01",
        "end_date": "2027-01-01",
    }
    inv_res = await async_client.post(
        "/api/v1/academic/academic-years", json=invalid_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert inv_res.status_code == 400


@pytest.mark.asyncio
async def test_06_semester(async_client: AsyncClient, db_session: AsyncSession):
    """6. Semester creation within academic year & unique semester number."""
    inst = Institution(name="PES Univ", code="PESU")
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)

    ay = AcademicYear(
        institution_id=inst.id,
        name="2026-27",
        start_date=date(2026, 8, 1),
        end_date=date(2027, 5, 31),
    )
    db_session.add(ay)
    await db_session.commit()
    await db_session.refresh(ay)

    _, admin_token = await create_user_helper(
        db_session, "admin@pes.edu", UserRole.INSTITUTION_ADMIN, institution_id=inst.id
    )

    sem_payload = {
        "academic_year_id": ay.id,
        "semester_number": 1,
        "label": "Semester 1",
        "start_date": "2026-08-01",
        "end_date": "2026-12-20",
    }
    res = await async_client.post(
        "/api/v1/academic/semesters", json=sem_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 201
    assert res.json()["semester_number"] == 1

    # Duplicate semester number -> 409
    dup_res = await async_client.post(
        "/api/v1/academic/semesters", json=sem_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert dup_res.status_code == 409


@pytest.mark.asyncio
async def test_07_batch(async_client: AsyncClient, db_session: AsyncSession):
    """7. Batch cohort creation & validation (admission_year < graduation_year)."""
    inst = Institution(name="RVCE", code="RVCE")
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)

    dept = Department(institution_id=inst.id, name="Electronics", code="ECE")
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)

    prog = Program(department_id=dept.id, name="B.Tech ECE", code="BE-ECE", degree_type="B.Tech", duration_years=4)
    db_session.add(prog)
    await db_session.commit()
    await db_session.refresh(prog)

    _, admin_token = await create_user_helper(
        db_session, "admin@rvce.edu", UserRole.INSTITUTION_ADMIN, institution_id=inst.id
    )

    batch_payload = {
        "institution_id": inst.id,
        "program_id": prog.id,
        "admission_year": 2023,
        "graduation_year": 2027,
        "label": "2023-2027",
    }
    res = await async_client.post(
        "/api/v1/academic/batches", json=batch_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 201
    assert res.json()["label"] == "2023-2027"

    # Duplicate batch label -> 409
    dup_res = await async_client.post(
        "/api/v1/academic/batches", json=batch_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert dup_res.status_code == 409

    # Invalid years -> 400
    inv_payload = {
        "institution_id": inst.id,
        "program_id": prog.id,
        "admission_year": 2027,
        "graduation_year": 2023,
        "label": "2027-2023",
    }
    inv_res = await async_client.post(
        "/api/v1/academic/batches", json=inv_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert inv_res.status_code == 400


@pytest.mark.asyncio
async def test_08_section(async_client: AsyncClient, db_session: AsyncSession):
    """8. Section creation within batch & unique section name per batch."""
    inst = Institution(name="MSRIT", code="MSRIT")
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)

    dept = Department(institution_id=inst.id, name="Civil", code="CIVIL")
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)

    prog = Program(department_id=dept.id, name="B.Tech Civil", code="BTECH-CIVIL", degree_type="B.Tech", duration_years=4)
    db_session.add(prog)
    await db_session.commit()
    await db_session.refresh(prog)

    batch = Batch(institution_id=inst.id, program_id=prog.id, admission_year=2024, graduation_year=2028, label="2024-2028")
    db_session.add(batch)
    await db_session.commit()
    await db_session.refresh(batch)

    _, admin_token = await create_user_helper(
        db_session, "admin@msrit.edu", UserRole.INSTITUTION_ADMIN, institution_id=inst.id
    )

    sec_payload = {"batch_id": batch.id, "name": "A", "capacity": 60}
    res = await async_client.post(
        "/api/v1/academic/sections", json=sec_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 201
    assert res.json()["name"] == "A"

    # Duplicate section name in same batch -> 409
    dup_res = await async_client.post(
        "/api/v1/academic/sections", json=sec_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert dup_res.status_code == 409


@pytest.mark.asyncio
async def test_09_course(async_client: AsyncClient, db_session: AsyncSession):
    """9. Course creation & unique course code within institution."""
    inst = Institution(name="SJCE", code="SJCE")
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)

    dept = Department(institution_id=inst.id, name="CSE", code="CSE")
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)

    _, admin_token = await create_user_helper(
        db_session, "admin@sjce.edu", UserRole.INSTITUTION_ADMIN, institution_id=inst.id
    )

    course_payload = {
        "institution_id": inst.id,
        "department_id": dept.id,
        "code": "CS101",
        "title": "Data Structures & Algorithms",
        "credits": 4.0,
        "course_type": "core",
    }
    res = await async_client.post(
        "/api/v1/academic/courses", json=course_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 201
    assert res.json()["code"] == "CS101"

    # Duplicate course code in same institution -> 409
    dup_res = await async_client.post(
        "/api/v1/academic/courses", json=course_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert dup_res.status_code == 409


@pytest.mark.asyncio
async def test_10_course_offering(async_client: AsyncClient, db_session: AsyncSession):
    """10. Course offering connecting Course + AcademicYear + Semester + Section."""
    inst = Institution(name="Inst Offering", code="IO01")
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)

    dept = Department(institution_id=inst.id, name="CSE", code="CSE")
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)

    prog = Program(department_id=dept.id, name="B.Tech CSE", code="BCSE", degree_type="B.Tech", duration_years=4)
    db_session.add(prog)
    await db_session.commit()
    await db_session.refresh(prog)

    batch = Batch(institution_id=inst.id, program_id=prog.id, admission_year=2023, graduation_year=2027, label="2023-27")
    db_session.add(batch)
    await db_session.commit()
    await db_session.refresh(batch)

    sec = Section(batch_id=batch.id, name="A", capacity=60)
    db_session.add(sec)

    ay = AcademicYear(institution_id=inst.id, name="2026-27", start_date=date(2026, 8, 1), end_date=date(2027, 5, 31))
    db_session.add(ay)
    await db_session.commit()
    await db_session.refresh(ay)

    sem = Semester(academic_year_id=ay.id, semester_number=1, label="Sem 1", start_date=date(2026, 8, 1), end_date=date(2026, 12, 15))
    db_session.add(sem)

    course = Course(institution_id=inst.id, department_id=dept.id, code="CS201", title="Database Systems", credits=3.0)
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(sec)
    await db_session.refresh(sem)
    await db_session.refresh(course)

    _, admin_token = await create_user_helper(
        db_session, "admin@io01.edu", UserRole.INSTITUTION_ADMIN, institution_id=inst.id
    )

    offering_payload = {
        "course_id": course.id,
        "academic_year_id": ay.id,
        "semester_id": sem.id,
        "section_id": sec.id,
    }
    res = await async_client.post(
        "/api/v1/academic/course-offerings", json=offering_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 201

    # Duplicate offering for same section/slot -> 409
    dup_res = await async_client.post(
        "/api/v1/academic/course-offerings", json=offering_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert dup_res.status_code == 409


@pytest.mark.asyncio
async def test_11_student_academic_profile(async_client: AsyncClient, db_session: AsyncSession):
    """11. Student academic profile creation and linking to authenticated user."""
    inst = Institution(name="Student Inst", code="SI01")
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)

    dept = Department(institution_id=inst.id, name="CSE", code="CSE")
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)

    prog = Program(department_id=dept.id, name="B.Tech", code="BT", degree_type="B.Tech", duration_years=4)
    db_session.add(prog)
    await db_session.commit()
    await db_session.refresh(prog)

    batch = Batch(institution_id=inst.id, program_id=prog.id, admission_year=2023, graduation_year=2027, label="2023-27")
    db_session.add(batch)
    await db_session.commit()
    await db_session.refresh(batch)

    student_user, _ = await create_user_helper(db_session, "realstudent@si.edu", UserRole.STUDENT)
    _, admin_token = await create_user_helper(
        db_session, "admin@si.edu", UserRole.INSTITUTION_ADMIN, institution_id=inst.id
    )

    profile_payload = {
        "user_id": student_user.id,
        "institution_id": inst.id,
        "program_id": prog.id,
        "batch_id": batch.id,
        "enrollment_number": "1SI23CS001",
        "admission_year": 2023,
        "graduation_year": 2027,
    }
    res = await async_client.post(
        "/api/v1/academic/student-profiles", json=profile_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["enrollment_number"] == "1SI23CS001"
    assert data["academic_status"] == "active"


@pytest.mark.asyncio
async def test_12_teacher_academic_profile(async_client: AsyncClient, db_session: AsyncSession):
    """12. Teacher academic profile creation and linking."""
    inst = Institution(name="Teacher Inst", code="TI01")
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)

    dept = Department(institution_id=inst.id, name="CSE", code="CSE")
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)

    teacher_user, _ = await create_user_helper(db_session, "prof.smith@ti.edu", UserRole.TEACHER)
    _, admin_token = await create_user_helper(
        db_session, "admin@ti.edu", UserRole.INSTITUTION_ADMIN, institution_id=inst.id
    )

    teacher_payload = {
        "user_id": teacher_user.id,
        "institution_id": inst.id,
        "department_id": dept.id,
        "designation": "Associate Professor",
        "employee_id": "EMP-CSE-042",
    }
    res = await async_client.post(
        "/api/v1/academic/teacher-profiles", json=teacher_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["employee_id"] == "EMP-CSE-042"
    assert data["designation"] == "Associate Professor"


@pytest.mark.asyncio
async def test_13_and_15_enrollment_and_duplicate_prevention(async_client: AsyncClient, db_session: AsyncSession):
    """13 & 15. Student enrollment in course offering and duplicate enrollment prevention."""
    inst = Institution(name="Enroll Inst", code="EI01")
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)

    dept = Department(institution_id=inst.id, name="CSE", code="CSE")
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)

    prog = Program(department_id=dept.id, name="B.Tech", code="BT", degree_type="B.Tech", duration_years=4)
    db_session.add(prog)
    await db_session.commit()
    await db_session.refresh(prog)

    batch = Batch(institution_id=inst.id, program_id=prog.id, admission_year=2023, graduation_year=2027, label="2023-27")
    db_session.add(batch)
    await db_session.commit()
    await db_session.refresh(batch)

    sec = Section(batch_id=batch.id, name="A")
    ay = AcademicYear(institution_id=inst.id, name="2026-27", start_date=date(2026, 8, 1), end_date=date(2027, 5, 31))
    db_session.add(sec)
    db_session.add(ay)
    await db_session.commit()
    await db_session.refresh(sec)
    await db_session.refresh(ay)

    sem = Semester(academic_year_id=ay.id, semester_number=1, label="Sem 1", start_date=date(2026, 8, 1), end_date=date(2026, 12, 15))
    course = Course(institution_id=inst.id, department_id=dept.id, code="CS301", title="OS")
    db_session.add(sem)
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(sem)
    await db_session.refresh(course)

    offering = CourseOffering(course_id=course.id, academic_year_id=ay.id, semester_id=sem.id, section_id=sec.id)
    db_session.add(offering)
    await db_session.commit()
    await db_session.refresh(offering)

    student_user, _ = await create_user_helper(db_session, "stu_enroll@ei.edu", UserRole.STUDENT)
    student_prof = StudentAcademicProfile(
        user_id=student_user.id,
        institution_id=inst.id,
        program_id=prog.id,
        batch_id=batch.id,
        enrollment_number="ENROLL101",
        admission_year=2023,
        graduation_year=2027,
    )
    db_session.add(student_prof)
    await db_session.commit()
    await db_session.refresh(student_prof)

    _, admin_token = await create_user_helper(
        db_session, "admin@ei.edu", UserRole.INSTITUTION_ADMIN, institution_id=inst.id
    )

    enroll_payload = {"student_profile_id": student_prof.id, "course_offering_id": offering.id}
    res = await async_client.post(
        "/api/v1/academic/enrollments", json=enroll_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 201
    assert res.json()["enrollment_status"] == "enrolled"

    # Duplicate enrollment prevention -> 409 Conflict
    dup_res = await async_client.post(
        "/api/v1/academic/enrollments", json=enroll_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert dup_res.status_code == 409


@pytest.mark.asyncio
async def test_14_and_16_teaching_assignment_and_duplicate_prevention(async_client: AsyncClient, db_session: AsyncSession):
    """14 & 16. Teaching assignment creation and duplicate assignment prevention."""
    inst = Institution(name="Assign Inst", code="AI01")
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)

    dept = Department(institution_id=inst.id, name="CSE", code="CSE")
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)

    prog = Program(department_id=dept.id, name="B.Tech", code="BT", degree_type="B.Tech", duration_years=4)
    db_session.add(prog)
    await db_session.commit()
    await db_session.refresh(prog)

    batch = Batch(institution_id=inst.id, program_id=prog.id, admission_year=2023, graduation_year=2027, label="2023-27")
    db_session.add(batch)
    await db_session.commit()
    await db_session.refresh(batch)

    sec = Section(batch_id=batch.id, name="A")
    ay = AcademicYear(institution_id=inst.id, name="2026-27", start_date=date(2026, 8, 1), end_date=date(2027, 5, 31))
    db_session.add_all([sec, ay])
    await db_session.commit()
    await db_session.refresh(sec)
    await db_session.refresh(ay)

    sem = Semester(academic_year_id=ay.id, semester_number=1, label="Sem 1", start_date=date(2026, 8, 1), end_date=date(2026, 12, 15))
    course = Course(institution_id=inst.id, department_id=dept.id, code="CS401", title="Compiler Design")
    db_session.add_all([sem, course])
    await db_session.commit()
    await db_session.refresh(sem)
    await db_session.refresh(course)

    offering = CourseOffering(course_id=course.id, academic_year_id=ay.id, semester_id=sem.id, section_id=sec.id)
    db_session.add(offering)
    await db_session.commit()
    await db_session.refresh(offering)

    teacher_user, _ = await create_user_helper(db_session, "dr.alan@ai01.edu", UserRole.TEACHER)
    teacher_prof = TeacherAcademicProfile(
        user_id=teacher_user.id,
        institution_id=inst.id,
        department_id=dept.id,
        designation="Professor",
        employee_id="TCH-007",
    )
    db_session.add(teacher_prof)
    await db_session.commit()
    await db_session.refresh(teacher_prof)

    _, admin_token = await create_user_helper(
        db_session, "admin@ai01.edu", UserRole.INSTITUTION_ADMIN, institution_id=inst.id
    )

    assign_payload = {
        "teacher_profile_id": teacher_prof.id,
        "course_offering_id": offering.id,
        "assignment_role": "lead_instructor",
    }
    res = await async_client.post(
        "/api/v1/academic/teaching-assignments", json=assign_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 201
    assert res.json()["assignment_role"] == "lead_instructor"

    # Duplicate teaching assignment prevention -> 409 Conflict
    dup_res = await async_client.post(
        "/api/v1/academic/teaching-assignments", json=assign_payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert dup_res.status_code == 409


@pytest.mark.asyncio
async def test_17_student_cannot_modify_academic_structure(async_client: AsyncClient, db_session: AsyncSession):
    """17. Student attempting to modify structural entities (courses, depts) is rejected."""
    _, student_token = await create_user_helper(db_session, "student_mod@dhruva.ai", UserRole.STUDENT)

    # Department
    dept_res = await async_client.post(
        "/api/v1/academic/departments",
        json={"institution_id": "dummy", "name": "Hack Dept", "code": "HACK"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert dept_res.status_code == 403

    # Course
    course_res = await async_client.post(
        "/api/v1/academic/courses",
        json={"institution_id": "dummy", "department_id": "dummy", "code": "CS000", "title": "Fake Course"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert course_res.status_code == 403


@pytest.mark.asyncio
async def test_18_student_cannot_self_assign_academic_profile(async_client: AsyncClient, db_session: AsyncSession):
    """18. Student cannot assign themselves to an institution/profile through public request."""
    student_user, student_token = await create_user_helper(db_session, "student_self@dhruva.ai", UserRole.STUDENT)

    res = await async_client.post(
        "/api/v1/academic/student-profiles",
        json={
            "user_id": student_user.id,
            "institution_id": "target-inst",
            "program_id": "target-prog",
            "batch_id": "target-batch",
            "enrollment_number": "HACKED_ROLL",
            "admission_year": 2023,
            "graduation_year": 2027,
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_19_student_cannot_access_another_students_private_profile(async_client: AsyncClient, db_session: AsyncSession):
    """19. Student cannot access another student's private profile."""
    inst = Institution(name="Iso Inst", code="ISO01")
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)

    dept = Department(institution_id=inst.id, name="CSE", code="CSE")
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)

    prog = Program(department_id=dept.id, name="B.Tech", code="BT", degree_type="B.Tech", duration_years=4)
    db_session.add(prog)
    await db_session.commit()
    await db_session.refresh(prog)

    batch = Batch(institution_id=inst.id, program_id=prog.id, admission_year=2023, graduation_year=2027, label="23-27")
    db_session.add(batch)
    await db_session.commit()
    await db_session.refresh(batch)

    stu1, token1 = await create_user_helper(db_session, "stu1@iso.edu", UserRole.STUDENT)
    stu2, token2 = await create_user_helper(db_session, "stu2@iso.edu", UserRole.STUDENT)

    prof1 = StudentAcademicProfile(
        user_id=stu1.id, institution_id=inst.id, program_id=prog.id, batch_id=batch.id, enrollment_number="ROLL-1", admission_year=2023, graduation_year=2027
    )
    prof2 = StudentAcademicProfile(
        user_id=stu2.id, institution_id=inst.id, program_id=prog.id, batch_id=batch.id, enrollment_number="ROLL-2", admission_year=2023, graduation_year=2027
    )
    db_session.add_all([prof1, prof2])
    await db_session.commit()

    # Stu1 accesses their own profile via /me -> 200
    res_me = await async_client.get("/api/v1/academic/student-profiles/me", headers={"Authorization": f"Bearer {token1}"})
    assert res_me.status_code == 200
    assert res_me.json()["enrollment_number"] == "ROLL-1"

    # Stu1 attempts to access Stu2's profile -> 403 Forbidden
    res_other = await async_client.get(
        f"/api/v1/academic/student-profiles/{stu2.id}", headers={"Authorization": f"Bearer {token1}"}
    )
    assert res_other.status_code == 403


@pytest.mark.asyncio
async def test_20_and_21_teacher_offering_and_student_scoping(async_client: AsyncClient, db_session: AsyncSession):
    """20 & 21. Teacher cannot access unrelated course offerings; can access authorized enrolled students."""
    inst = Institution(name="Scope Inst", code="SCO01")
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)

    dept = Department(institution_id=inst.id, name="CSE", code="CSE")
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)

    prog = Program(department_id=dept.id, name="B.Tech", code="BT", degree_type="B.Tech", duration_years=4)
    db_session.add(prog)
    await db_session.commit()
    await db_session.refresh(prog)

    batch = Batch(institution_id=inst.id, program_id=prog.id, admission_year=2023, graduation_year=2027, label="2023-27")
    db_session.add(batch)
    await db_session.commit()
    await db_session.refresh(batch)

    sec = Section(batch_id=batch.id, name="A")
    ay = AcademicYear(institution_id=inst.id, name="2026-27", start_date=date(2026, 8, 1), end_date=date(2027, 5, 31))
    db_session.add_all([sec, ay])
    await db_session.commit()
    await db_session.refresh(sec)
    await db_session.refresh(ay)


    sem = Semester(academic_year_id=ay.id, semester_number=1, label="Sem 1", start_date=date(2026, 8, 1), end_date=date(2026, 12, 15))
    course1 = Course(institution_id=inst.id, department_id=dept.id, code="CS101", title="Algorithms")
    course2 = Course(institution_id=inst.id, department_id=dept.id, code="CS102", title="Networks")
    db_session.add_all([sem, course1, course2])
    await db_session.commit()

    offering1 = CourseOffering(course_id=course1.id, academic_year_id=ay.id, semester_id=sem.id, section_id=sec.id)
    offering2 = CourseOffering(course_id=course2.id, academic_year_id=ay.id, semester_id=sem.id, section_id=sec.id)
    db_session.add_all([offering1, offering2])
    await db_session.commit()

    teacher_user, teacher_token = await create_user_helper(db_session, "teacher.auth@sco.edu", UserRole.TEACHER)
    teacher_prof = TeacherAcademicProfile(
        user_id=teacher_user.id, institution_id=inst.id, department_id=dept.id, designation="Asst Prof", employee_id="SCO-T1"
    )
    db_session.add(teacher_prof)
    await db_session.commit()

    # Assign teacher to offering 1 only
    assign1 = TeachingAssignment(teacher_profile_id=teacher_prof.id, course_offering_id=offering1.id, assignment_role="lead_instructor")
    db_session.add(assign1)

    # Student enrolled in offering 1
    stu_user, _ = await create_user_helper(db_session, "stu.enrolled@sco.edu", UserRole.STUDENT)
    stu_prof = StudentAcademicProfile(
        user_id=stu_user.id, institution_id=inst.id, program_id=prog.id, batch_id=batch.id, enrollment_number="SCO-S1", admission_year=2023, graduation_year=2027
    )
    db_session.add(stu_prof)
    await db_session.commit()

    enrollment = StudentEnrollment(student_profile_id=stu_prof.id, course_offering_id=offering1.id)
    db_session.add(enrollment)
    await db_session.commit()

    # 20. Teacher accessing authorized offering 1 -> 200
    res_off1 = await async_client.get(
        f"/api/v1/academic/course-offerings/{offering1.id}", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert res_off1.status_code == 200

    # 20. Teacher accessing unrelated offering 2 -> 403 Forbidden
    res_off2 = await async_client.get(
        f"/api/v1/academic/course-offerings/{offering2.id}", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert res_off2.status_code == 403

    # 21. Teacher accessing enrolled student's profile -> 200
    res_stu_prof = await async_client.get(
        f"/api/v1/academic/student-profiles/{stu_user.id}", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert res_stu_prof.status_code == 200
    assert res_stu_prof.json()["enrollment_number"] == "SCO-S1"


@pytest.mark.asyncio
async def test_22_hod_department_scoping(async_client: AsyncClient, db_session: AsyncSession):
    """22. HOD can create courses within their institution, rejected outside."""
    inst1 = Institution(name="HOD Inst 1", code="HOD01")
    inst2 = Institution(name="HOD Inst 2", code="HOD02")
    db_session.add_all([inst1, inst2])
    await db_session.commit()

    dept1 = Department(institution_id=inst1.id, name="CSE", code="CSE")
    dept2 = Department(institution_id=inst2.id, name="CSE", code="CSE")
    db_session.add_all([dept1, dept2])
    await db_session.commit()

    _, hod_token = await create_user_helper(
        db_session, "hod@hod01.edu", UserRole.HOD, institution_id=inst1.id
    )

    # HOD in institution 1 creates course in institution 1 -> 201
    res1 = await async_client.post(
        "/api/v1/academic/courses",
        json={"institution_id": inst1.id, "department_id": dept1.id, "code": "CS-HOD1", "title": "Advanced AI"},
        headers={"Authorization": f"Bearer {hod_token}"},
    )
    assert res1.status_code == 201

    # HOD in institution 1 attempts to create course in institution 2 -> 403
    res2 = await async_client.post(
        "/api/v1/academic/courses",
        json={"institution_id": inst2.id, "department_id": dept2.id, "code": "CS-HOD2", "title": "Other AI"},
        headers={"Authorization": f"Bearer {hod_token}"},
    )
    assert res2.status_code == 403


@pytest.mark.asyncio
async def test_23_and_24_institution_admin_and_super_admin_scoping(async_client: AsyncClient, db_session: AsyncSession):
    """23 & 24. Institution Admin cannot cross-manage institutions; Super Admin has platform-wide access."""
    inst1 = Institution(name="Alpha Univ", code="ALPHA")
    inst2 = Institution(name="Beta Univ", code="BETA")
    db_session.add_all([inst1, inst2])
    await db_session.commit()

    _, inst_admin_token = await create_user_helper(
        db_session, "admin@alpha.edu", UserRole.INSTITUTION_ADMIN, institution_id=inst1.id
    )
    _, super_token = await create_user_helper(
        db_session, "superadmin@platform.io", UserRole.SUPER_ADMIN
    )

    # 23. Admin of Alpha attempts to create department in Beta -> 403 Forbidden
    res_cross = await async_client.post(
        "/api/v1/academic/departments",
        json={"institution_id": inst2.id, "name": "Illegal Dept", "code": "ILL"},
        headers={"Authorization": f"Bearer {inst_admin_token}"},
    )
    assert res_cross.status_code == 403

    # 24. Super Admin creates department in Beta -> 201 Created
    res_super = await async_client.post(
        "/api/v1/academic/departments",
        json={"institution_id": inst2.id, "name": "Beta ECE", "code": "ECE"},
        headers={"Authorization": f"Bearer {super_token}"},
    )
    assert res_super.status_code == 201
    assert res_super.json()["code"] == "ECE"


@pytest.mark.asyncio
async def test_25_foreign_key_integrity(async_client: AsyncClient, db_session: AsyncSession):
    """25. Foreign-key cascading: Deleting an institution cascades to its departments."""
    inst = Institution(name="Cascade Univ", code="CASC")
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)

    dept = Department(institution_id=inst.id, name="Cascade Dept", code="CDEPT")
    db_session.add(dept)
    await db_session.commit()

    # Delete institution directly in DB
    await db_session.delete(inst)
    await db_session.commit()

    # Department should no longer exist
    res = await async_client.get(f"/api/v1/academic/departments/{dept.id}", headers={"Authorization": "Bearer fake"})
    assert res.status_code in (401, 404)


@pytest.mark.asyncio
async def test_26_invalid_relationships_rejected(async_client: AsyncClient, db_session: AsyncSession):
    """26. Invalid foreign-key relationships rejected with 404."""
    inst = Institution(name="Relation Univ", code="REL01")
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)

    _, admin_token = await create_user_helper(
        db_session, "admin@rel01.edu", UserRole.INSTITUTION_ADMIN, institution_id=inst.id
    )

    # Non-existent department ID -> 404
    prog_res = await async_client.post(
        "/api/v1/academic/programs",
        json={
            "department_id": "non-existent-dept-id",
            "name": "Ghost Program",
            "code": "GHOST",
            "degree_type": "B.Tech",
            "duration_years": 4,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert prog_res.status_code == 404
    assert "not found" in prog_res.json()["detail"].lower()
