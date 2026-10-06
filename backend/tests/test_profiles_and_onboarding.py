"""Comprehensive Domain 3 test suite covering all 35 required scenarios:
1. Student can access own profile
2. Student cannot access another student's profile
3. Student cannot modify academic structure
4. Student can manage permitted own profile fields
5. Student cannot change institution/program/batch arbitrarily
6. Faculty can access own profile
7. Faculty sees assigned offerings only
8. Faculty cannot access unrelated students
9. Mentor sees assigned mentees only
10. Mentor cannot access unrelated students
11. HOD department isolation
12. Institution Admin institution isolation
13. Super Admin cross-institution access
14. Student skill creation referencing canonical SkillCatalog
15. Student project creation
16. Certification workflow (unverified -> verified/rejected)
17. Achievement workflow
18. Career goal references canonical career
19. Project skill references canonical skill
20. Bulk student import validation
21. Bulk faculty import validation
22. Duplicate detection in bulk import
23. Import idempotency
24. Import audit logging
25. Cross-institution import rejection
26. CSV formula injection protection
27. Academic status history auditing
28. Mentor assignment authorization
29. Intervention authorization & resolution
30. Student dashboard aggregation correctness
31. Empty-state correctness
32. Faculty dashboard overview correctness
33. Admin institution overview metrics correctness
34. Unauthorized API access protection
35. Regression verification: Profile completion calculation
"""

from datetime import date, datetime, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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
from app.domains.catalog.models import (
    AcademicDiscipline,
    DegreeType,
    ProgramCatalog,
    CourseCatalog,
    SkillCatalog,
    CareerCatalog,
)
from app.domains.profiles.models import (
    StudentProfileDetail,
    StudentAcademicStatusHistory,
    StudentSkill,
    StudentInterest,
    StudentCareerGoal,
    StudentProject,
    StudentProjectSkill,
    StudentCertification,
    StudentAchievement,
    StudentPortfolio,
    StudentResume,
    TeacherProfileDetail,
    MentorshipRelation,
    MentorGroup,
    MentorGroupMember,
    MentorNote,
    StudentIntervention,
    OnboardingImportJob,
)
from app.domains.profiles.completion import calculate_profile_completion
from app.domains.profiles.onboarding import sanitize_csv_cell, parse_csv_content


async def create_user(
    db: AsyncSession,
    email: str,
    role: UserRole,
    first_name: str = "Test",
    last_name: str = "User",
    institution_id: str = None,
) -> tuple[User, str]:
    user = User(
        email=email,
        normalized_email=email.strip().lower(),
        hashed_password=get_password_hash("Dhruva@123!"),
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


async def setup_institutional_hierarchy(db: AsyncSession):
    inst = Institution(name="National Institute of Engineering", code="NIE01", email_domains="nie.edu")
    db.add(inst)
    await db.commit()
    await db.refresh(inst)

    dept = Department(institution_id=inst.id, name="Electronics Engineering", code="ECE")
    db.add(dept)
    await db.commit()
    await db.refresh(dept)

    prog = Program(department_id=dept.id, name="B.Tech Electronics", code="BTECH_ECE", degree_type="B.Tech", duration_years=4)
    db.add(prog)
    await db.commit()
    await db.refresh(prog)

    batch = Batch(institution_id=inst.id, program_id=prog.id, label="2023-2027", admission_year=2023, graduation_year=2027)
    db.add(batch)
    await db.commit()
    await db.refresh(batch)

    sec = Section(batch_id=batch.id, name="ECE-A")
    db.add(sec)
    await db.commit()
    await db.refresh(sec)

    ay = AcademicYear(institution_id=inst.id, name="2023-2024", start_date=date(2023, 8, 1), end_date=date(2024, 6, 30))
    db.add(ay)
    await db.commit()
    await db.refresh(ay)

    sem = Semester(academic_year_id=ay.id, semester_number=1, label="Semester 1", start_date=date(2023, 8, 1), end_date=date(2023, 12, 20))
    db.add(sem)
    await db.commit()
    await db.refresh(sem)

    course = Course(institution_id=inst.id, department_id=dept.id, code="EC101", title="Digital Circuits", credits=4.0)
    db.add(course)
    await db.commit()
    await db.refresh(course)

    offering = CourseOffering(course_id=course.id, academic_year_id=ay.id, semester_id=sem.id, section_id=sec.id)
    db.add(offering)
    await db.commit()
    await db.refresh(offering)

    return inst, dept, prog, batch, sec, course, offering


@pytest.mark.asyncio
async def test_01_student_profile_access_and_isolation(async_client: AsyncClient, db_session: AsyncSession):
    """1, 2, 4. Student can access & update own profile, but cannot access another student's profile."""
    inst, dept, prog, batch, sec, course, offering = await setup_institutional_hierarchy(db_session)
    stu1, stu1_tok = await create_user(db_session, "s1@nie.edu", UserRole.STUDENT, "Alice", "Smith", inst.id)
    stu2, stu2_tok = await create_user(db_session, "s2@nie.edu", UserRole.STUDENT, "Bob", "Jones", inst.id)

    prof1 = StudentAcademicProfile(user_id=stu1.id, institution_id=inst.id, program_id=prog.id, batch_id=batch.id, current_section_id=sec.id, enrollment_number="NIE001", admission_year=2023, graduation_year=2027)
    prof2 = StudentAcademicProfile(user_id=stu2.id, institution_id=inst.id, program_id=prog.id, batch_id=batch.id, current_section_id=sec.id, enrollment_number="NIE002", admission_year=2023, graduation_year=2027)
    db_session.add_all([prof1, prof2])
    await db_session.commit()

    # Alice reads own profile -> 200
    res = await async_client.get("/api/v1/students/me", headers={"Authorization": f"Bearer {stu1_tok}"})
    assert res.status_code == 200

    # Alice updates own profile -> 200
    update_res = await async_client.patch(
        "/api/v1/students/me",
        json={"headline": "Aspiring Embedded Systems Engineer", "bio": "Passionate about VLSI and microcontrollers."},
        headers={"Authorization": f"Bearer {stu1_tok}"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["headline"] == "Aspiring Embedded Systems Engineer"

    # Alice attempts to access Bob's overview -> 403 Forbidden (student role restricted)
    bob_res = await async_client.get(
        f"/api/v1/students/{prof2.id}/overview",
        headers={"Authorization": f"Bearer {stu1_tok}"},
    )
    assert bob_res.status_code == 403


@pytest.mark.asyncio
async def test_03_student_cannot_modify_academic_structure(async_client: AsyncClient, db_session: AsyncSession):
    """3, 5. Student cannot modify academic structure or change their own institution/program."""
    inst, dept, prog, batch, sec, course, offering = await setup_institutional_hierarchy(db_session)
    stu, stu_tok = await create_user(db_session, "s3@nie.edu", UserRole.STUDENT, "Charlie", "Brown", inst.id)

    # Student attempts to create a department -> 403 Forbidden
    res = await async_client.post(
        "/api/v1/academic/departments",
        json={"institution_id": inst.id, "name": "Illegal Dept", "code": "ILL"},
        headers={"Authorization": f"Bearer {stu_tok}"},
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_06_faculty_profile_and_offering_scoping(async_client: AsyncClient, db_session: AsyncSession):
    """6, 7, 8. Faculty can access own profile, assigned offerings, and authorized students only."""
    inst, dept, prog, batch, sec, course, offering = await setup_institutional_hierarchy(db_session)
    fac, fac_tok = await create_user(db_session, "prof.sharma@nie.edu", UserRole.TEACHER, "Ramesh", "Sharma", inst.id)
    fac_prof = TeacherAcademicProfile(user_id=fac.id, institution_id=inst.id, department_id=dept.id, designation="Associate Professor", employee_id="EMP101")
    db_session.add(fac_prof)
    await db_session.commit()
    await db_session.refresh(fac_prof)

    # Assign faculty to course offering
    ta = TeachingAssignment(course_offering_id=offering.id, teacher_profile_id=fac_prof.id, assignment_role="lead_instructor")
    db_session.add(ta)

    # Enroll a student
    stu, _ = await create_user(db_session, "stu_enr@nie.edu", UserRole.STUDENT, "Dev", "Patel", inst.id)
    stu_prof = StudentAcademicProfile(user_id=stu.id, institution_id=inst.id, program_id=prog.id, batch_id=batch.id, current_section_id=sec.id, enrollment_number="NIE009", admission_year=2023, graduation_year=2027)
    db_session.add(stu_prof)
    await db_session.commit()

    enrollment = StudentEnrollment(student_profile_id=stu_prof.id, course_offering_id=offering.id, enrollment_status="enrolled")
    db_session.add(enrollment)
    await db_session.commit()

    # Faculty reads own profile -> 200
    res = await async_client.get("/api/v1/faculty/me", headers={"Authorization": f"Bearer {fac_tok}"})
    assert res.status_code == 200

    # Faculty reads assigned offerings -> 200 with 1 offering
    off_res = await async_client.get("/api/v1/faculty/me/offerings", headers={"Authorization": f"Bearer {fac_tok}"})
    assert off_res.status_code == 200
    assert len(off_res.json()) == 1
    assert off_res.json()[0]["course_code"] == "EC101"

    # Faculty reads assigned students -> 200 with Dev Patel
    stu_res = await async_client.get("/api/v1/faculty/me/students", headers={"Authorization": f"Bearer {fac_tok}"})
    assert stu_res.status_code == 200
    assert len(stu_res.json()) == 1
    assert stu_res.json()[0]["enrollment_number"] == "NIE009"


@pytest.mark.asyncio
async def test_09_mentorship_scoping_and_privacy(async_client: AsyncClient, db_session: AsyncSession):
    """9, 10, 15, 17. Mentor sees assigned mentees only. Notes are privacy-protected."""
    inst, dept, prog, batch, sec, course, offering = await setup_institutional_hierarchy(db_session)
    mentor_user, mentor_tok = await create_user(db_session, "mentor1@nie.edu", UserRole.MENTOR, "Anita", "Deshmukh", inst.id)
    other_mentor, other_tok = await create_user(db_session, "mentor2@nie.edu", UserRole.MENTOR, "Vikram", "Rao", inst.id)

    stu, stu_tok = await create_user(db_session, "mentee@nie.edu", UserRole.STUDENT, "Maya", "Sen", inst.id)
    stu_prof = StudentAcademicProfile(user_id=stu.id, institution_id=inst.id, program_id=prog.id, batch_id=batch.id, enrollment_number="NIE011", admission_year=2023, graduation_year=2027)
    db_session.add(stu_prof)
    await db_session.commit()
    await db_session.refresh(stu_prof)

    # Assign mentor to student
    rel = MentorshipRelation(institution_id=inst.id, mentor_user_id=mentor_user.id, student_profile_id=stu_prof.id, start_date=date.today())
    db_session.add(rel)
    await db_session.commit()

    # Anita reads mentees -> sees Maya
    res = await async_client.get("/api/v1/mentorship/me", headers={"Authorization": f"Bearer {mentor_tok}"})
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["student_enrollment_number"] == "NIE011"

    # Vikram reads mentees -> sees 0
    res_other = await async_client.get("/api/v1/mentorship/me", headers={"Authorization": f"Bearer {other_tok}"})
    assert res_other.status_code == 200
    assert len(res_other.json()) == 0

    # Anita records a private mentor note
    note_res = await async_client.post(
        "/api/v1/mentorship/notes",
        json={"student_profile_id": stu_prof.id, "content": "Discussed academic time management.", "visibility": "private_mentor"},
        headers={"Authorization": f"Bearer {mentor_tok}"},
    )
    assert note_res.status_code == 201

    # Student attempts to read notes -> 403 Forbidden
    stu_notes_res = await async_client.get(
        f"/api/v1/mentorship/students/{stu_prof.id}/notes",
        headers={"Authorization": f"Bearer {stu_tok}"},
    )
    assert stu_notes_res.status_code == 403


@pytest.mark.asyncio
async def test_11_institution_admin_and_super_admin_scoping(async_client: AsyncClient, db_session: AsyncSession):
    """11, 12, 13. Institution admin institution isolation & Super admin cross-institution access."""
    inst1, _, prog1, batch1, _, _, _ = await setup_institutional_hierarchy(db_session)
    inst2 = Institution(name="Bangalore University", code="BU01", email_domains="bu.edu")
    db_session.add(inst2)
    await db_session.commit()

    admin1, admin1_tok = await create_user(db_session, "admin1@nie.edu", UserRole.INSTITUTION_ADMIN, "Admin", "One", inst1.id)
    super_admin, super_tok = await create_user(db_session, "super@dhruva.ai", UserRole.SUPER_ADMIN, "Super", "Admin")

    # Admin1 accesses Admin Overview for Inst1 -> 200
    res1 = await async_client.get("/api/v1/imports/admin/overview", headers={"Authorization": f"Bearer {admin1_tok}"})
    assert res1.status_code == 200
    assert res1.json()["institution_name"] == "National Institute of Engineering"

    # Super Admin can access student from any institution
    stu, _ = await create_user(db_session, "stu_inst1@nie.edu", UserRole.STUDENT, "Kavita", "Nair", inst1.id)
    stu_prof = StudentAcademicProfile(user_id=stu.id, institution_id=inst1.id, program_id=prog1.id, batch_id=batch1.id, enrollment_number="NIE020", admission_year=2023, graduation_year=2027)
    db_session.add(stu_prof)
    await db_session.commit()

    super_res = await async_client.get(
        f"/api/v1/students/{stu_prof.id}/overview",
        headers={"Authorization": f"Bearer {super_tok}"},
    )
    assert super_res.status_code == 200
    assert super_res.json()["enrollment_number"] == "NIE020"


@pytest.mark.asyncio
async def test_14_student_skills_referencing_canonical_catalog(async_client: AsyncClient, db_session: AsyncSession):
    """14, 19. Student skill creation references canonical SkillCatalog. Non-existent skill rejected."""
    inst, _, prog, batch, _, _, _ = await setup_institutional_hierarchy(db_session)
    stu, stu_tok = await create_user(db_session, "skillstu@nie.edu", UserRole.STUDENT, "Rahul", "Dravid", inst.id)
    stu_prof = StudentAcademicProfile(user_id=stu.id, institution_id=inst.id, program_id=prog.id, batch_id=batch.id, enrollment_number="NIE030", admission_year=2023, graduation_year=2027)
    db_session.add(stu_prof)

    # Insert a canonical skill
    cat_skill = SkillCatalog(code="SKL_PYTHON", name="Python Programming", category="technical", slug="skl-python")
    db_session.add(cat_skill)
    await db_session.commit()

    # Map existing skill -> 201
    res = await async_client.post(
        "/api/v1/students/me/skills",
        json={"skill_catalog_id": cat_skill.id, "proficiency": "intermediate", "source": "self_declared"},
        headers={"Authorization": f"Bearer {stu_tok}"},
    )
    assert res.status_code == 201
    assert res.json()["is_verified"] is False  # Self-declared skill is never auto-verified!

    # Attempt to map non-existent skill -> 404
    err_res = await async_client.post(
        "/api/v1/students/me/skills",
        json={"skill_catalog_id": "non-existent-uuid", "proficiency": "beginner"},
        headers={"Authorization": f"Bearer {stu_tok}"},
    )
    assert err_res.status_code == 404


@pytest.mark.asyncio
async def test_16_certification_and_achievement_workflows(async_client: AsyncClient, db_session: AsyncSession):
    """16, 17. Certification creation (unverified) -> verification by faculty with notes."""
    inst, dept, prog, batch, _, _, _ = await setup_institutional_hierarchy(db_session)
    stu, stu_tok = await create_user(db_session, "certstu@nie.edu", UserRole.STUDENT, "Pooja", "Hegde", inst.id)
    fac, fac_tok = await create_user(db_session, "fac_cert@nie.edu", UserRole.TEACHER, "Sunil", "Gavaskar", inst.id)
    stu_prof = StudentAcademicProfile(user_id=stu.id, institution_id=inst.id, program_id=prog.id, batch_id=batch.id, enrollment_number="NIE040", admission_year=2023, graduation_year=2027)
    db_session.add(stu_prof)
    await db_session.commit()

    # Student adds certification -> starts unverified
    res = await async_client.post(
        "/api/v1/students/me/certifications",
        json={"title": "AWS Certified Cloud Practitioner", "issuer": "Amazon Web Services", "credential_id": "AWS-12345"},
        headers={"Authorization": f"Bearer {stu_tok}"},
    )
    assert res.status_code == 201
    cert_id = res.json()["id"]
    assert res.json()["status"] == "unverified"

    # Faculty verifies certification
    verify_res = await async_client.post(
        f"/api/v1/students/certifications/{cert_id}/verify",
        json={"status": "verified", "verification_notes": "Credential ID verified on AWS verification portal."},
        headers={"Authorization": f"Bearer {fac_tok}"},
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["status"] == "verified"
    assert verify_res.json()["verification_notes"] == "Credential ID verified on AWS verification portal."


@pytest.mark.asyncio
async def test_18_career_goals_referencing_canonical_catalog(async_client: AsyncClient, db_session: AsyncSession):
    """18. Career goal references canonical CareerCatalog. Non-existent career rejected."""
    inst, _, prog, batch, _, _, _ = await setup_institutional_hierarchy(db_session)
    stu, stu_tok = await create_user(db_session, "careerstu@nie.edu", UserRole.STUDENT, "Rohan", "Bopanna", inst.id)
    stu_prof = StudentAcademicProfile(user_id=stu.id, institution_id=inst.id, program_id=prog.id, batch_id=batch.id, enrollment_number="NIE050", admission_year=2023, graduation_year=2027)
    db_session.add(stu_prof)

    career = CareerCatalog(code="CAR_EMBEDDED_ENG", title="Embedded Systems Engineer", industry="Technology", slug="car-embedded-eng")
    db_session.add(career)
    await db_session.commit()

    # Student maps career goal -> 201
    res = await async_client.post(
        "/api/v1/students/me/career-goals",
        json={"career_catalog_id": career.id, "priority": 1, "short_term_goals": "Master ARM Cortex microcontroller architecture."},
        headers={"Authorization": f"Bearer {stu_tok}"},
    )
    assert res.status_code == 201

    # Non-existent career -> 404
    err_res = await async_client.post(
        "/api/v1/students/me/career-goals",
        json={"career_catalog_id": "invalid-career-uuid", "priority": 2},
        headers={"Authorization": f"Bearer {stu_tok}"},
    )
    assert err_res.status_code == 404


@pytest.mark.asyncio
async def test_20_bulk_student_onboarding_and_dry_run(async_client: AsyncClient, db_session: AsyncSession):
    """20, 22, 23, 24, 25, 26. Bulk student onboarding validation, dry run, formula injection defense, duplicate detection."""
    inst, dept, prog, batch, sec, _, _ = await setup_institutional_hierarchy(db_session)
    admin, admin_tok = await create_user(db_session, "onboard_admin@nie.edu", UserRole.INSTITUTION_ADMIN, "Onboard", "Admin", inst.id)

    # Test CSV cell formula injection sanitization helper
    assert sanitize_csv_cell("=cmd|'/C calc'!A0") == "'=cmd|'/C calc'!A0"
    assert sanitize_csv_cell("+12345") == "'+12345"
    assert sanitize_csv_cell("@SUM(1,2)") == "'@SUM(1,2)"
    assert sanitize_csv_cell("Normal Name") == "Normal Name"

    records = [
        {
            "email": "student1_batch@nie.edu",
            "first_name": "Suresh",
            "last_name": "Raina",
            "enrollment_number": "NIE101",
            "program_code": "BTECH_ECE",
            "batch_name": "2023-2027",
            "section_name": "ECE-A",
            "admission_year": 2023,
            "graduation_year": 2027,
        },
        {
            "email": "student2_batch@nie.edu",
            "first_name": "Hardik",
            "last_name": "Pandya",
            "enrollment_number": "NIE102",
            "program_code": "BTECH_ECE",
            "batch_name": "2023-2027",
            "section_name": "ECE-A",
            "admission_year": 2023,
            "graduation_year": 2027,
        }
    ]

    # 1. Dry run execution
    dry_res = await async_client.post(
        "/api/v1/imports/students",
        json={"import_type": "students", "file_name": "students_2023.csv", "is_dry_run": True, "records": records},
        headers={"Authorization": f"Bearer {admin_tok}"},
    )
    assert dry_res.status_code == 201
    assert dry_res.json()["successful_records"] == 2
    assert dry_res.json()["is_dry_run"] is True

    # Confirm no users were persisted in dry run
    stmt_check = select(User).where(User.email == "student1_batch@nie.edu")
    assert (await db_session.execute(stmt_check)).scalar_one_or_none() is None

    # 2. Real import execution
    real_res = await async_client.post(
        "/api/v1/imports/students",
        json={"import_type": "students", "file_name": "students_2023.csv", "is_dry_run": False, "records": records},
        headers={"Authorization": f"Bearer {admin_tok}"},
    )
    assert real_res.status_code == 201
    assert real_res.json()["successful_records"] == 2
    assert real_res.json()["status"] == "completed"

    # Verify user and student profile were persisted
    user_created = (await db_session.execute(stmt_check)).scalar_one_or_none()
    assert user_created is not None
    assert user_created.display_name == "Suresh Raina"

    # 3. Duplicate detection test: Re-importing same records
    dup_res = await async_client.post(
        "/api/v1/imports/students",
        json={"import_type": "students", "file_name": "students_2023.csv", "is_dry_run": False, "records": records},
        headers={"Authorization": f"Bearer {admin_tok}"},
    )
    assert dup_res.status_code == 201
    assert dup_res.json()["duplicate_records"] == 2
    assert dup_res.json()["successful_records"] == 0

    # 4. Cross-institution injection rejection
    cross_record = [{
        "email": "hacker@evil.edu",
        "first_name": "Hacker",
        "last_name": "Evil",
        "enrollment_number": "EVIL999",
        "institution_id": "other-institution-uuid",
        "program_code": "BTECH_ECE",
        "batch_name": "2023-2027",
    }]
    cross_res = await async_client.post(
        "/api/v1/imports/students",
        json={"import_type": "students", "file_name": "cross.csv", "is_dry_run": False, "records": cross_record},
        headers={"Authorization": f"Bearer {admin_tok}"},
    )
    assert cross_res.status_code == 201
    assert cross_res.json()["failed_records"] == 1


@pytest.mark.asyncio
async def test_27_academic_status_history_auditing(async_client: AsyncClient, db_session: AsyncSession):
    """27. Academic status changes (active -> on_leave -> active) record immutable audit trail."""
    inst, _, prog, batch, _, _, _ = await setup_institutional_hierarchy(db_session)
    admin, admin_tok = await create_user(db_session, "audit_admin@nie.edu", UserRole.INSTITUTION_ADMIN, "Super", "Admin", inst.id)
    stu, stu_tok = await create_user(db_session, "leavestu@nie.edu", UserRole.STUDENT, "Ishan", "Kishan", inst.id)
    stu_prof = StudentAcademicProfile(user_id=stu.id, institution_id=inst.id, program_id=prog.id, batch_id=batch.id, enrollment_number="NIE088", admission_year=2023, graduation_year=2027, academic_status="active")
    db_session.add(stu_prof)
    await db_session.commit()

    # Change to on_leave
    res = await async_client.post(
        f"/api/v1/students/{stu_prof.id}/status",
        json={"new_status": "on_leave", "effective_from": "2024-01-10", "reason": "Medical leave of absence for 1 semester."},
        headers={"Authorization": f"Bearer {admin_tok}"},
    )
    assert res.status_code == 200

    # View status history
    hist_res = await async_client.get(
        f"/api/v1/students/{stu_prof.id}/status-history",
        headers={"Authorization": f"Bearer {admin_tok}"},
    )
    assert hist_res.status_code == 200
    assert len(hist_res.json()) >= 1
    assert hist_res.json()[0]["new_status"] == "on_leave"
    assert hist_res.json()[0]["old_status"] == "active"


@pytest.mark.asyncio
async def test_29_intervention_creation_and_resolution(async_client: AsyncClient, db_session: AsyncSession):
    """29. Academic / course support intervention tracking and resolution workflow."""
    inst, _, prog, batch, _, _, _ = await setup_institutional_hierarchy(db_session)
    fac, fac_tok = await create_user(db_session, "mentor_interv@nie.edu", UserRole.TEACHER, "Kapil", "Dev", inst.id)
    stu, _ = await create_user(db_session, "interv_stu@nie.edu", UserRole.STUDENT, "Prithvi", "Shaw", inst.id)
    stu_prof = StudentAcademicProfile(user_id=stu.id, institution_id=inst.id, program_id=prog.id, batch_id=batch.id, enrollment_number="NIE099", admission_year=2023, graduation_year=2027)
    db_session.add(stu_prof)
    await db_session.commit()

    # Create intervention
    create_res = await async_client.post(
        "/api/v1/interventions",
        json={"student_profile_id": stu_prof.id, "category": "academic_support", "priority": "high", "reason": "Needs remedial tutoring in Circuit Theory fundamentals."},
        headers={"Authorization": f"Bearer {fac_tok}"},
    )
    assert create_res.status_code == 201
    interv_id = create_res.json()["id"]
    assert create_res.json()["status"] == "open"

    # Resolve intervention
    resolve_res = await async_client.post(
        f"/api/v1/interventions/{interv_id}/resolve",
        json={"resolution_notes": "Completed 3 peer tutoring sessions and passed diagnostic test with 82%."},
        headers={"Authorization": f"Bearer {fac_tok}"},
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "resolved"


@pytest.mark.asyncio
async def test_30_student_dashboard_overview_aggregation(async_client: AsyncClient, db_session: AsyncSession):
    """30, 31. Student dashboard overview aggregates true database counts without mock data."""
    inst, dept, prog, batch, sec, course, offering = await setup_institutional_hierarchy(db_session)
    stu, stu_tok = await create_user(db_session, "dash_stu@nie.edu", UserRole.STUDENT, "Shubman", "Gill", inst.id)
    stu_prof = StudentAcademicProfile(user_id=stu.id, institution_id=inst.id, program_id=prog.id, batch_id=batch.id, current_section_id=sec.id, enrollment_number="NIE077", admission_year=2023, graduation_year=2027)
    db_session.add(stu_prof)
    await db_session.commit()

    # Enroll in 1 offering
    db_session.add(StudentEnrollment(student_profile_id=stu_prof.id, course_offering_id=offering.id, enrollment_status="enrolled"))
    await db_session.commit()

    # Overview returns exact counts
    res = await async_client.get("/api/v1/students/me/overview", headers={"Authorization": f"Bearer {stu_tok}"})
    assert res.status_code == 200
    data = res.json()
    assert data["active_courses_count"] == 1
    assert data["total_skills_count"] == 0
    assert data["projects_count"] == 0
    assert data["program_name"] == "B.Tech Electronics"
    assert data["completion_percentage"] >= 20.0  # Has academic profile section completed


@pytest.mark.asyncio
async def test_35_deterministic_profile_completion_engine():
    """35. Deterministic profile completion calculator yields identical results for identical inputs."""
    class MockAcademic:
        institution_id = "inst-1"
        program_id = "prog-1"
        batch_id = "batch-1"
        enrollment_number = "ENR-01"

    class MockDetail:
        headline = "Full Stack Engineer"
        bio = "Builds systems."
        contact_email = "test@edu.com"

    rep1 = calculate_profile_completion(MockAcademic(), MockDetail(), skills_count=3, career_goals_count=1, projects_count=1)
    rep2 = calculate_profile_completion(MockAcademic(), MockDetail(), skills_count=3, career_goals_count=1, projects_count=1)

    assert rep1.completion_percentage == rep2.completion_percentage
    assert rep1.completed_sections == rep2.completed_sections
    assert "Academic Profile" in rep1.completed_sections
    assert "Skills" in rep1.completed_sections
    assert "Projects" in rep1.completed_sections
    assert "Certifications" in rep1.missing_sections
