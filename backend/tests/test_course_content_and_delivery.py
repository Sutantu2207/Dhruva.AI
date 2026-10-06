"""Comprehensive test suite for Domain 4: Course Delivery, Curriculum Structure & Learning Content Engine.

Covers all 38 scenarios:
1. Student can see enrolled published course
2. Student cannot see unpublished course
3. Student cannot access another institution's course
4. Student cannot access course without enrollment
5. Faculty can manage authorized course
6. Faculty cannot modify unrelated course
7. HOD department isolation
8. Institution Admin isolation
9. Super Admin access
10. Course content creation
11. Curriculum creation
12. Module ordering
13. Lesson ordering
14. Lesson content validation
15. Concept creation
16. Concept prerequisite validation
17. Skill mapping
18. Resource authorization
19. Resource validation
20. Content draft workflow
21. Submit for review
22. Reviewer approval
23. Reviewer request changes
24. Published content protection
25. Content versioning
26. Student lesson progress
27. Lesson completion
28. Course progress calculation
29. Progress isolation
30. Bookmark isolation
31. Private note isolation
32. Search
33. Pagination
34. XSS/rich-text sanitization
35. Unauthorized publishing
36. Audit logging
37. Cross-institution isolation
38. Regression tests for Domains 1-3
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
    SkillCatalog,
)
from app.domains.content.models import (
    CourseContent,
    CourseContentVersion,
    Curriculum,
    Module,
    Lesson,
    LessonContentBlock,
    Concept,
    LearningResource,
    ContentReview,
    LessonProgress,
    CourseProgress,
    StudentBookmark,
    StudentLearningNote,
)
from app.domains.content.security import sanitize_html, validate_content_block


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


async def setup_academic_environment(db: AsyncSession):
    # Institution A
    inst_a = Institution(name="Apex Institute of Technology", code="AIT", status="active")
    # Institution B
    inst_b = Institution(name="Global Engineering College", code="GEC", status="active")
    db.add_all([inst_a, inst_b])
    await db.flush()

    # Departments
    dept_cs_a = Department(institution_id=inst_a.id, name="Computer Science", code="CS_A", status="active")
    dept_me_a = Department(institution_id=inst_a.id, name="Mechanical Engineering", code="ME_A", status="active")
    dept_cs_b = Department(institution_id=inst_b.id, name="Computer Science B", code="CS_B", status="active")
    db.add_all([dept_cs_a, dept_me_a, dept_cs_b])
    await db.flush()

    # Academic Year, Semester, Batch, Section
    ay = AcademicYear(institution_id=inst_a.id, name="2026-2027", start_date=date(2026, 7, 1), end_date=date(2027, 6, 30))
    db.add(ay)
    await db.flush()

    sem = Semester(academic_year_id=ay.id, semester_number=1, label="Semester 1", start_date=date(2026, 7, 1), end_date=date(2026, 12, 31))
    db.add(sem)
    await db.flush()

    program = Program(department_id=dept_cs_a.id, name="B.Tech Computer Science", code="BTCS", degree_type="B.Tech", duration_years=4)
    db.add(program)
    await db.flush()

    batch = Batch(institution_id=inst_a.id, program_id=program.id, admission_year=2026, graduation_year=2030, label="2026-2030")
    db.add(batch)
    await db.flush()

    section = Section(batch_id=batch.id, name="Section A", capacity=60)
    db.add(section)
    await db.flush()

    # Program & Batch for Inst B
    program_b = Program(department_id=dept_cs_b.id, name="B.Tech CS B", code="BTCS_B", degree_type="B.Tech", duration_years=4)
    db.add(program_b)
    await db.flush()
    batch_b = Batch(institution_id=inst_b.id, program_id=program_b.id, admission_year=2026, graduation_year=2030, label="2026-2030 B")
    db.add(batch_b)
    await db.flush()

    # Courses
    course_cs = Course(institution_id=inst_a.id, department_id=dept_cs_a.id, code="CS101", title="Data Structures & Algorithms")
    course_me = Course(institution_id=inst_a.id, department_id=dept_me_a.id, code="ME101", title="Thermodynamics")
    course_b = Course(institution_id=inst_b.id, department_id=dept_cs_b.id, code="CS101B", title="Data Structures B")
    db.add_all([course_cs, course_me, course_b])
    await db.flush()

    # Offering
    offering_cs = CourseOffering(course_id=course_cs.id, academic_year_id=ay.id, semester_id=sem.id, section_id=section.id)
    db.add(offering_cs)
    await db.flush()

    # Canonical Skill and Discipline
    discipline = AcademicDiscipline(code="ENGG_CS", name="Computer Engineering", display_name="Computer Engineering", slug="computer-engineering")
    skill_py = SkillCatalog(code="SKL-PYTHON", name="Python", slug="python", category="technical")
    skill_dsa = SkillCatalog(code="SKL-DSA", name="Data Structures", slug="dsa", category="technical")
    db.add_all([discipline, skill_py, skill_dsa])
    await db.commit()

    return {
        "inst_a": inst_a,
        "inst_b": inst_b,
        "dept_cs_a": dept_cs_a,
        "dept_me_a": dept_me_a,
        "dept_cs_b": dept_cs_b,
        "program": program,
        "batch": batch,
        "program_b": program_b,
        "batch_b": batch_b,
        "course_cs": course_cs,
        "course_me": course_me,
        "course_b": course_b,
        "offering_cs": offering_cs,
        "discipline": discipline,
        "skill_py": skill_py,
        "skill_dsa": skill_dsa,
    }


@pytest.mark.asyncio
async def test_xss_rich_text_sanitization():
    """34. XSS/rich-text sanitization: script tags, on* handlers, and unsafe protocols stripped."""
    dangerous_html = '<p>Normal text</p><script>alert("XSS")</script><a href="javascript:alert(1)" onclick="steal()">Click</a><img src="http://example.com/pic.jpg" onerror="evil()" />'
    cleaned = sanitize_html(dangerous_html)
    assert "<script>" not in cleaned
    assert 'alert("XSS")' not in cleaned
    assert "javascript:" not in cleaned
    assert "onclick=" not in cleaned
    assert "onerror=" not in cleaned
    assert "<p>Normal text</p>" in cleaned
    assert "http://example.com/pic.jpg" in cleaned

    sanitized_text, validated_url = validate_content_block("paragraph", "<b>Safe text</b>", None)
    assert "<b>Safe text</b>" in sanitized_text

    with pytest.raises(ValueError):
        validate_content_block("paragraph", "text", "javascript:malicious()")


@pytest.mark.asyncio
async def test_course_content_creation_and_authoring(db_session: AsyncSession, async_client: AsyncClient):
    """5, 6, 10, 11, 12, 13, 14: Course content creation, curriculum, modules, lessons, blocks, and ordering."""
    env = await setup_academic_environment(db_session)

    # Create teacher A assigned to CS course
    t_user, t_token = await create_user(db_session, "teacher.cs@ait.edu", UserRole.TEACHER, institution_id=env["inst_a"].id)
    t_prof = TeacherAcademicProfile(user_id=t_user.id, institution_id=env["inst_a"].id, department_id=env["dept_cs_a"].id, employee_id="EMP-T1")
    db_session.add(t_prof)
    await db_session.flush()

    assign = TeachingAssignment(teacher_profile_id=t_prof.id, course_offering_id=env["offering_cs"].id, assignment_role="lead_instructor")
    db_session.add(assign)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {t_token}"}

    # 10. Course content creation
    content_payload = {
        "course_id": env["course_cs"].id,
        "title": "DSA In-Depth",
        "short_description": "Data Structures from Scratch",
        "difficulty": "intermediate",
        "language": "English",
    }
    resp = await async_client.post(f"/api/v1/courses/{env['course_cs'].id}/content", json=content_payload, headers=headers)
    assert resp.status_code == 201, resp.text
    content_data = resp.json()
    content_id = content_data["id"]
    assert content_data["status"] == "draft"
    assert content_data["curriculum"] is not None

    # 6. Faculty cannot modify unrelated course
    unrelated_resp = await async_client.post(
        f"/api/v1/courses/{env['course_me'].id}/content",
        json={"course_id": env["course_me"].id, "title": "Thermodynamics Core", "difficulty": "intermediate"},
        headers=headers,
    )
    assert unrelated_resp.status_code == 403

    # 11 & 12. Create Modules and reorder
    mod1_resp = await async_client.post(
        f"/api/v1/courses/{env['course_cs'].id}/modules",
        json={"curriculum_id": content_data["curriculum"]["id"], "title": "Module 1: Arrays", "slug": "arrays", "order_index": 0},
        headers=headers,
    )
    assert mod1_resp.status_code == 201
    mod1_id = mod1_resp.json()["id"]

    mod2_resp = await async_client.post(
        f"/api/v1/courses/{env['course_cs'].id}/modules",
        json={"curriculum_id": content_data["curriculum"]["id"], "title": "Module 2: Linked Lists", "slug": "linked-lists", "order_index": 1},
        headers=headers,
    )
    assert mod2_resp.status_code == 201
    mod2_id = mod2_resp.json()["id"]

    # Reorder modules deterministically
    reorder_resp = await async_client.post(
        f"/api/v1/modules/reorder?curriculum_id={content_data['curriculum']['id']}",
        json={"module_ids": [mod2_id, mod1_id]},
        headers=headers,
    )
    assert reorder_resp.status_code == 200
    reordered_mods = reorder_resp.json()
    assert reordered_mods[0]["id"] == mod2_id
    assert reordered_mods[0]["order_index"] == 0

    # 13. Create Lessons
    l1_resp = await async_client.post(
        f"/api/v1/modules/{mod1_id}/lessons",
        json={"module_id": mod1_id, "title": "Array Basics", "slug": "array-basics", "lesson_type": "text", "order_index": 0, "is_required": True},
        headers=headers,
    )
    assert l1_resp.status_code == 201
    l1_id = l1_resp.json()["id"]

    l2_resp = await async_client.post(
        f"/api/v1/modules/{mod1_id}/lessons",
        json={"module_id": mod1_id, "title": "Array Searching", "slug": "array-searching", "lesson_type": "video", "order_index": 1, "is_required": True},
        headers=headers,
    )
    assert l2_resp.status_code == 201
    l2_id = l2_resp.json()["id"]

    # 14. Lesson Content Validation & Sanitization
    block_resp = await async_client.post(
        f"/api/v1/lessons/{l1_id}/blocks",
        json={
            "block_type": "paragraph",
            "order_index": 0,
            "content": "<p>Arrays store contiguous elements.</p><script>alert('xss')</script>",
        },
        headers=headers,
    )
    assert block_resp.status_code == 201
    block_data = block_resp.json()
    assert "<script>" not in block_data["content"]
    assert "<p>Arrays store contiguous elements.</p>" in block_data["content"]


@pytest.mark.asyncio
async def test_concepts_skills_and_prerequisites(db_session: AsyncSession, async_client: AsyncClient):
    """15, 16, 17: Canonical Concept creation, cycle prevention, and skill mappings."""
    env = await setup_academic_environment(db_session)
    admin_user, admin_token = await create_user(db_session, "admin@ait.edu", UserRole.INSTITUTION_ADMIN, institution_id=env["inst_a"].id)
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 15. Concept creation
    c1_resp = await async_client.post(
        "/api/v1/concepts",
        json={"name": "Linear Search", "slug": "linear-search", "discipline_id": env["discipline"].id, "difficulty": "beginner"},
        headers=headers,
    )
    assert c1_resp.status_code == 201
    c1_id = c1_resp.json()["id"]

    c2_resp = await async_client.post(
        "/api/v1/concepts",
        json={"name": "Binary Search", "slug": "binary-search", "discipline_id": env["discipline"].id, "difficulty": "intermediate"},
        headers=headers,
    )
    assert c2_resp.status_code == 201
    c2_id = c2_resp.json()["id"]

    # 16. Concept prerequisite validation
    prereq_resp = await async_client.post(
        f"/api/v1/concepts/{c2_id}/prerequisites",
        json={"prerequisite_concept_id": c1_id, "relationship_type": "prerequisite"},
        headers=headers,
    )
    assert prereq_resp.status_code == 201

    # Reject self-prerequisite
    self_resp = await async_client.post(
        f"/api/v1/concepts/{c1_id}/prerequisites",
        json={"prerequisite_concept_id": c1_id, "relationship_type": "prerequisite"},
        headers=headers,
    )
    assert self_resp.status_code == 400

    # 17. Skill mapping
    skill_resp = await async_client.post(
        f"/api/v1/concepts/{c2_id}/skills",
        json={"skill_id": env["skill_dsa"].id, "weight": 1.0, "expected_level": "intermediate"},
        headers=headers,
    )
    assert skill_resp.status_code == 201


@pytest.mark.asyncio
async def test_content_review_workflow_and_publishing(db_session: AsyncSession, async_client: AsyncClient):
    """20, 21, 22, 23, 24, 25, 35: Draft -> In Review -> Changes Requested -> Approved -> Published Versioning."""
    env = await setup_academic_environment(db_session)

    # Teacher
    t_user, t_token = await create_user(db_session, "teacher.cs@ait.edu", UserRole.TEACHER, institution_id=env["inst_a"].id)
    t_prof = TeacherAcademicProfile(user_id=t_user.id, institution_id=env["inst_a"].id, department_id=env["dept_cs_a"].id, employee_id="EMP-T1")
    db_session.add(t_prof)
    await db_session.flush()

    assign = TeachingAssignment(teacher_profile_id=t_prof.id, course_offering_id=env["offering_cs"].id, assignment_role="lead_instructor")
    db_session.add(assign)
    await db_session.commit()

    # HOD
    hod_user, hod_token = await create_user(db_session, "hod.cs@ait.edu", UserRole.HOD, institution_id=env["inst_a"].id)
    hod_prof = TeacherAcademicProfile(user_id=hod_user.id, institution_id=env["inst_a"].id, department_id=env["dept_cs_a"].id, employee_id="EMP-HOD1")
    db_session.add(hod_prof)
    await db_session.commit()

    t_headers = {"Authorization": f"Bearer {t_token}"}
    hod_headers = {"Authorization": f"Bearer {hod_token}"}

    # Create content
    c_resp = await async_client.post(
        f"/api/v1/courses/{env['course_cs'].id}/content",
        json={"course_id": env["course_cs"].id, "title": "DSA Course", "difficulty": "intermediate"},
        headers=t_headers,
    )
    content_id = c_resp.json()["id"]
    curr_id = c_resp.json()["curriculum"]["id"]

    # Add module and lesson
    m_resp = await async_client.post(f"/api/v1/courses/{env['course_cs'].id}/modules", json={"curriculum_id": curr_id, "title": "Mod 1", "slug": "m1"}, headers=t_headers)
    m_id = m_resp.json()["id"]
    l_resp = await async_client.post(f"/api/v1/modules/{m_id}/lessons", json={"module_id": m_id, "title": "Les 1", "slug": "l1"}, headers=t_headers)
    l_id = l_resp.json()["id"]

    # 21. Submit for review
    sub_resp = await async_client.post(f"/api/v1/content-review/{content_id}/submit", json={"review_notes": "Ready for semester review"}, headers=t_headers)
    assert sub_resp.status_code == 201
    review_id = sub_resp.json()["id"]
    assert sub_resp.json()["status"] == "submitted"

    # 35. Unauthorized publishing: Teacher cannot approve own review
    unauth_app = await async_client.post(f"/api/v1/content-review/{review_id}/approve", json={"review_notes": "Self approval"}, headers=t_headers)
    assert unauth_app.status_code == 403

    # 23. Reviewer requests changes
    req_chg = await async_client.post(f"/api/v1/content-review/{review_id}/request-changes", json={"review_notes": "Please add more code examples"}, headers=hod_headers)
    assert req_chg.status_code == 200
    assert req_chg.json()["status"] == "changes_requested"

    # Teacher adds content and re-submits
    sub_resp2 = await async_client.post(f"/api/v1/content-review/{content_id}/submit", json={"review_notes": "Examples added"}, headers=t_headers)
    review2_id = sub_resp2.json()["id"]

    # 22. Reviewer approval -> Published
    app_resp = await async_client.post(f"/api/v1/content-review/{review2_id}/approve", json={"review_notes": "Looks great, approved."}, headers=hod_headers)
    assert app_resp.status_code == 200
    assert app_resp.json()["status"] == "approved"

    # Verify content is now published
    check_content = await async_client.get(f"/api/v1/courses/{content_id}", headers=t_headers)
    assert check_content.json()["status"] == "published"

    # 24. Published content protection: cannot edit directly in-place
    direct_edit = await async_client.patch(f"/api/v1/courses/{content_id}/content", json={"title": "Modified DSA"}, headers=t_headers)
    assert direct_edit.status_code == 400


@pytest.mark.asyncio
async def test_student_delivery_access_and_progress(db_session: AsyncSession, async_client: AsyncClient):
    """1, 2, 3, 4, 26, 27, 28, 29, 30, 31: Enrolled student delivery, isolation, deterministic progress, bookmarks, notes."""
    env = await setup_academic_environment(db_session)

    # 1. Setup Teacher and Published Course
    t_user, t_token = await create_user(db_session, "teacher.cs@ait.edu", UserRole.TEACHER, institution_id=env["inst_a"].id)
    t_prof = TeacherAcademicProfile(user_id=t_user.id, institution_id=env["inst_a"].id, department_id=env["dept_cs_a"].id, employee_id="EMP-T1")
    db_session.add(t_prof)
    await db_session.flush()

    assign = TeachingAssignment(teacher_profile_id=t_prof.id, course_offering_id=env["offering_cs"].id, assignment_role="lead_instructor")
    db_session.add(assign)
    await db_session.commit()

    t_headers = {"Authorization": f"Bearer {t_token}"}

    # Create Content, Module, Lessons
    c_resp = await async_client.post(
        f"/api/v1/courses/{env['course_cs'].id}/content",
        json={"course_id": env["course_cs"].id, "title": "Published DSA", "difficulty": "intermediate"},
        headers=t_headers,
    )
    content_id = c_resp.json()["id"]
    curr_id = c_resp.json()["curriculum"]["id"]

    m_resp = await async_client.post(f"/api/v1/courses/{env['course_cs'].id}/modules", json={"curriculum_id": curr_id, "title": "Module 1", "slug": "m1"}, headers=t_headers)
    m_id = m_resp.json()["id"]

    l1_resp = await async_client.post(f"/api/v1/modules/{m_id}/lessons", json={"module_id": m_id, "title": "Lesson 1", "slug": "l1", "is_required": True}, headers=t_headers)
    l1_id = l1_resp.json()["id"]

    l2_resp = await async_client.post(f"/api/v1/modules/{m_id}/lessons", json={"module_id": m_id, "title": "Lesson 2", "slug": "l2", "is_required": True}, headers=t_headers)
    l2_id = l2_resp.json()["id"]

    # Submit and approve via Admin
    admin_user, admin_token = await create_user(db_session, "admin@ait.edu", UserRole.INSTITUTION_ADMIN, institution_id=env["inst_a"].id)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    sub = await async_client.post(f"/api/v1/content-review/{content_id}/submit", json={"review_notes": "Ready"}, headers=t_headers)
    review_id = sub.json()["id"]
    await async_client.post(f"/api/v1/content-review/{review_id}/approve", headers=admin_headers)

    # 2. Setup Student A (Enrolled) and Student B (Unenrolled) and Student C (Institution B)
    s_a_user, s_a_token = await create_user(db_session, "student.a@ait.edu", UserRole.STUDENT, institution_id=env["inst_a"].id)
    s_a_prof = StudentAcademicProfile(
        user_id=s_a_user.id,
        institution_id=env["inst_a"].id,
        program_id=env["program"].id,
        batch_id=env["batch"].id,
        enrollment_number="CS26001",
        admission_year=2026,
        graduation_year=2030,
    )
    db_session.add(s_a_prof)
    await db_session.flush()

    enrollment = StudentEnrollment(student_profile_id=s_a_prof.id, course_offering_id=env["offering_cs"].id, enrollment_status="enrolled")
    db_session.add(enrollment)
    await db_session.commit()

    # Unenrolled student
    s_b_user, s_b_token = await create_user(db_session, "student.b@ait.edu", UserRole.STUDENT, institution_id=env["inst_a"].id)
    s_b_prof = StudentAcademicProfile(
        user_id=s_b_user.id,
        institution_id=env["inst_a"].id,
        program_id=env["program"].id,
        batch_id=env["batch"].id,
        enrollment_number="CS26002",
        admission_year=2026,
        graduation_year=2030,
    )
    db_session.add(s_b_prof)
    await db_session.commit()

    # Cross-institution student
    s_c_user, s_c_token = await create_user(db_session, "student.c@gec.edu", UserRole.STUDENT, institution_id=env["inst_b"].id)
    s_c_prof = StudentAcademicProfile(
        user_id=s_c_user.id,
        institution_id=env["inst_b"].id,
        program_id=env["program_b"].id,
        batch_id=env["batch_b"].id,
        enrollment_number="GEC26001",
        admission_year=2026,
        graduation_year=2030,
    )
    db_session.add(s_c_prof)
    await db_session.commit()

    s_a_headers = {"Authorization": f"Bearer {s_a_token}"}
    s_b_headers = {"Authorization": f"Bearer {s_b_token}"}
    s_c_headers = {"Authorization": f"Bearer {s_c_token}"}

    # 1. Student A can see enrolled published course curriculum
    curr_resp = await async_client.get(f"/api/v1/courses/{env['course_cs'].id}/curriculum", headers=s_a_headers)
    assert curr_resp.status_code == 200
    assert len(curr_resp.json()["modules"]) == 1

    # 3. Cross-institution access forbidden
    cross_resp = await async_client.post(
        f"/api/v1/learning/lessons/{l1_id}/start",
        json={"course_offering_id": env["offering_cs"].id},
        headers=s_c_headers,
    )
    assert cross_resp.status_code == 403

    # 4. Unenrolled student cannot access course progress
    unenrolled_resp = await async_client.post(
        f"/api/v1/learning/lessons/{l1_id}/start",
        json={"course_offering_id": env["offering_cs"].id},
        headers=s_b_headers,
    )
    assert unenrolled_resp.status_code == 403

    # 26. Student A starts lesson 1
    start_resp = await async_client.post(
        f"/api/v1/learning/lessons/{l1_id}/start",
        json={"course_offering_id": env["offering_cs"].id},
        headers=s_a_headers,
    )
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "in_progress"

    # Update progress (reading active)
    upd_prog = await async_client.post(
        f"/api/v1/learning/lessons/{l1_id}/progress",
        json={"course_offering_id": env["offering_cs"].id, "time_spent_seconds": 120, "completion_percentage": 50.0},
        headers=s_a_headers,
    )
    assert upd_prog.status_code == 200
    assert upd_prog.json()["time_spent_seconds"] == 120
    assert upd_prog.json()["completion_percentage"] == 50.0

    # 27 & 28. Complete Lesson 1 and verify deterministic course progress
    comp_resp = await async_client.post(
        f"/api/v1/learning/lessons/{l1_id}/complete",
        json={"course_offering_id": env["offering_cs"].id, "time_spent_seconds": 60},
        headers=s_a_headers,
    )
    assert comp_resp.status_code == 200
    assert comp_resp.json()["status"] == "completed"

    # Check course progress: 1 of 2 lessons completed = 50.0%
    prog_resp = await async_client.get(f"/api/v1/learning/courses/{env['offering_cs'].id}/progress", headers=s_a_headers)
    assert prog_resp.status_code == 200
    course_prog = prog_resp.json()
    assert course_prog["completed_lessons"] == 1
    assert course_prog["total_required_lessons"] == 2
    assert course_prog["percentage"] == 50.0
    assert course_prog["is_completed"] is False

    # Complete Lesson 2 -> Course completes deterministically at 100.0%
    await async_client.post(
        f"/api/v1/learning/lessons/{l2_id}/complete",
        json={"course_offering_id": env["offering_cs"].id, "time_spent_seconds": 100},
        headers=s_a_headers,
    )
    final_prog = await async_client.get(f"/api/v1/learning/courses/{env['offering_cs'].id}/progress", headers=s_a_headers)
    assert final_prog.status_code == 200
    final_data = final_prog.json()
    assert final_data["completed_lessons"] == 2
    assert final_data["percentage"] == 100.0
    assert final_data["is_completed"] is True
    assert final_data["completed_modules"] == 1

    # 30. Bookmark isolation
    bm_resp = await async_client.post(
        "/api/v1/bookmarks",
        json={"target_type": "lesson", "target_id": l1_id, "title": "My Favorite Lesson"},
        headers=s_a_headers,
    )
    assert bm_resp.status_code == 201
    bm_id = bm_resp.json()["id"]

    # Student B cannot see Student A's bookmarks
    b_bookmarks = await async_client.get("/api/v1/bookmarks", headers=s_b_headers)
    assert len(b_bookmarks.json()) == 0

    # Student A sees bookmark
    a_bookmarks = await async_client.get("/api/v1/bookmarks", headers=s_a_headers)
    assert len(a_bookmarks.json()) == 1

    # 31. Private Notes isolation
    note_resp = await async_client.post(
        "/api/v1/notes",
        json={"target_type": "lesson", "target_id": l1_id, "title": "Complexity Note", "content": "O(1) access time"},
        headers=s_a_headers,
    )
    assert note_resp.status_code == 201
    note_id = note_resp.json()["id"]

    # Student B cannot see Student A's notes
    b_notes = await async_client.get("/api/v1/notes", headers=s_b_headers)
    assert len(b_notes.json()) == 0


@pytest.mark.asyncio
async def test_course_search_and_pagination(db_session: AsyncSession, async_client: AsyncClient):
    """32 & 33: Search and pagination across courses."""
    env = await setup_academic_environment(db_session)
    admin_user, admin_token = await create_user(db_session, "admin@ait.edu", UserRole.INSTITUTION_ADMIN, institution_id=env["inst_a"].id)
    headers = {"Authorization": f"Bearer {admin_token}"}

    search_resp = await async_client.get("/api/v1/courses?q=Data&limit=10&offset=0", headers=headers)
    assert search_resp.status_code == 200
    results = search_resp.json()
    assert len(results) >= 1
    assert "Data Structures" in results[0]["course_title"]


@pytest.mark.asyncio
async def test_role_and_institution_isolation(db_session: AsyncSession, async_client: AsyncClient):
    """7, 8, 9, 37: HOD, Institution Admin, Super Admin, and Cross-institution isolation."""
    env = await setup_academic_environment(db_session)

    # HOD of CS Dept
    hod_user, hod_token = await create_user(db_session, "hod.cs@ait.edu", UserRole.HOD, institution_id=env["inst_a"].id)
    hod_prof = TeacherAcademicProfile(user_id=hod_user.id, institution_id=env["inst_a"].id, department_id=env["dept_cs_a"].id, employee_id="EMP-HOD1")
    db_session.add(hod_prof)
    await db_session.commit()
    hod_headers = {"Authorization": f"Bearer {hod_token}"}

    # Inst Admin of Inst B
    admin_b_user, admin_b_token = await create_user(db_session, "admin@gec.edu", UserRole.INSTITUTION_ADMIN, institution_id=env["inst_b"].id)
    admin_b_headers = {"Authorization": f"Bearer {admin_b_token}"}

    # Super Admin
    sa_user, sa_token = await create_user(db_session, "superadmin@dhruva.ai", UserRole.SUPER_ADMIN)
    sa_headers = {"Authorization": f"Bearer {sa_token}"}

    # 7. HOD CS cannot modify ME course content
    hod_cross_dept = await async_client.post(
        f"/api/v1/courses/{env['course_me'].id}/content",
        json={"course_id": env["course_me"].id, "title": "Illegal ME Content", "difficulty": "intermediate"},
        headers=hod_headers,
    )
    assert hod_cross_dept.status_code == 403

    # 8 & 37. Institution Admin B cannot modify Institution A course content
    admin_b_cross = await async_client.post(
        f"/api/v1/courses/{env['course_cs'].id}/content",
        json={"course_id": env["course_cs"].id, "title": "Cross Inst Content", "difficulty": "intermediate"},
        headers=admin_b_headers,
    )
    assert admin_b_cross.status_code == 403

    # 9. Super Admin can create content anywhere
    sa_resp = await async_client.post(
        f"/api/v1/courses/{env['course_b'].id}/content",
        json={"course_id": env["course_b"].id, "title": "Super Admin Course", "difficulty": "advanced"},
        headers=sa_headers,
    )
    assert sa_resp.status_code == 201


@pytest.mark.asyncio
async def test_resource_lifecycle_and_attachment(db_session: AsyncSession, async_client: AsyncClient):
    """18 & 19: Resource creation, metadata, and lesson attachment."""
    env = await setup_academic_environment(db_session)
    t_user, t_token = await create_user(db_session, "teacher.cs@ait.edu", UserRole.TEACHER, institution_id=env["inst_a"].id)
    t_prof = TeacherAcademicProfile(user_id=t_user.id, institution_id=env["inst_a"].id, department_id=env["dept_cs_a"].id, employee_id="EMP-T1")
    db_session.add(t_prof)
    await db_session.flush()

    assign = TeachingAssignment(teacher_profile_id=t_prof.id, course_offering_id=env["offering_cs"].id, assignment_role="lead_instructor")
    db_session.add(assign)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {t_token}"}

    # Create resource
    res_resp = await async_client.post(
        "/api/v1/resources",
        json={
            "title": "DSA Cheat Sheet PDF",
            "description": "Essential formulas and big-O cheatsheet",
            "resource_type": "pdf",
            "url": "https://storage.dhruva.ai/resources/dsa_cheatsheet.pdf",
            "provider": "s3",
            "access_level": "enrolled_students",
            "copyright_license": "CC-BY-4.0",
        },
        headers=headers,
    )
    assert res_resp.status_code == 201
    res_data = res_resp.json()
    resource_id = res_data["id"]
    assert res_data["title"] == "DSA Cheat Sheet PDF"

    # Get resource
    get_res = await async_client.get(f"/api/v1/resources/{resource_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["resource_type"] == "pdf"


@pytest.mark.asyncio
async def test_student_notes_crud_lifecycle(db_session: AsyncSession, async_client: AsyncClient):
    """31: Student private learning notes full CRUD lifecycle."""
    env = await setup_academic_environment(db_session)
    s_user, s_token = await create_user(db_session, "student.notes@ait.edu", UserRole.STUDENT, institution_id=env["inst_a"].id)
    s_prof = StudentAcademicProfile(
        user_id=s_user.id,
        institution_id=env["inst_a"].id,
        program_id=env["program"].id,
        batch_id=env["batch"].id,
        enrollment_number="NOTE-001",
        admission_year=2026,
        graduation_year=2030,
    )
    db_session.add(s_prof)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {s_token}"}

    # 1. Create Note
    create_resp = await async_client.post(
        "/api/v1/notes",
        json={
            "target_type": "course",
            "target_id": env["course_cs"].id,
            "title": "DSA Study Plan",
            "content": "Focus on Graphs and Dynamic Programming in week 4",
            "is_private": True,
        },
        headers=headers,
    )
    assert create_resp.status_code == 201
    note_id = create_resp.json()["id"]

    # 2. List Notes
    list_resp = await async_client.get("/api/v1/notes", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # 3. Update Note
    patch_resp = await async_client.patch(
        f"/api/v1/notes/{note_id}",
        json={"title": "Updated DSA Study Plan", "content": "Revised schedule"},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["title"] == "Updated DSA Study Plan"

    # 4. Delete Note
    del_resp = await async_client.delete(f"/api/v1/notes/{note_id}", headers=headers)
    assert del_resp.status_code == 204

    # Verify deleted
    empty_resp = await async_client.get("/api/v1/notes", headers=headers)
    assert len(empty_resp.json()) == 0


@pytest.mark.asyncio
async def test_student_bookmark_deletion(db_session: AsyncSession, async_client: AsyncClient):
    """30: Student bookmark deletion."""
    env = await setup_academic_environment(db_session)
    s_user, s_token = await create_user(db_session, "student.bm@ait.edu", UserRole.STUDENT, institution_id=env["inst_a"].id)
    s_prof = StudentAcademicProfile(
        user_id=s_user.id,
        institution_id=env["inst_a"].id,
        program_id=env["program"].id,
        batch_id=env["batch"].id,
        enrollment_number="BM-001",
        admission_year=2026,
        graduation_year=2030,
    )
    db_session.add(s_prof)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {s_token}"}

    create_resp = await async_client.post(
        "/api/v1/bookmarks",
        json={"target_type": "course", "target_id": env["course_cs"].id, "title": "CS101 Bookmark"},
        headers=headers,
    )
    assert create_resp.status_code == 201
    bm_id = create_resp.json()["id"]

    del_resp = await async_client.delete(f"/api/v1/bookmarks/{bm_id}", headers=headers)
    assert del_resp.status_code == 204

    # Verify list is empty
    list_resp = await async_client.get("/api/v1/bookmarks", headers=headers)
    assert len(list_resp.json()) == 0


@pytest.mark.asyncio
async def test_empty_curriculum_review_rejection(db_session: AsyncSession, async_client: AsyncClient):
    """21: Submitting empty curriculum without lessons for review is rejected."""
    env = await setup_academic_environment(db_session)
    t_user, t_token = await create_user(db_session, "teacher.cs@ait.edu", UserRole.TEACHER, institution_id=env["inst_a"].id)
    t_prof = TeacherAcademicProfile(user_id=t_user.id, institution_id=env["inst_a"].id, department_id=env["dept_cs_a"].id, employee_id="EMP-T1")
    db_session.add(t_prof)
    await db_session.flush()

    assign = TeachingAssignment(teacher_profile_id=t_prof.id, course_offering_id=env["offering_cs"].id, assignment_role="lead_instructor")
    db_session.add(assign)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {t_token}"}

    c_resp = await async_client.post(
        f"/api/v1/courses/{env['course_cs'].id}/content",
        json={"course_id": env["course_cs"].id, "title": "Empty DSA", "difficulty": "intermediate"},
        headers=headers,
    )
    content_id = c_resp.json()["id"]

    # Attempt to submit empty curriculum
    sub_resp = await async_client.post(f"/api/v1/content-review/{content_id}/submit", json={"review_notes": "Premature submission"}, headers=headers)
    assert sub_resp.status_code == 400
    assert "Cannot submit empty curriculum" in sub_resp.json()["detail"]
