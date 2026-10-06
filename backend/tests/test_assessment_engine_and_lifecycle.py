"""Integration and unit tests for Domain 5: Assessment Engine, Question Banks, Evaluation & Evidence."""

import pytest
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from httpx import AsyncClient, ASGITransport
from app.main import app
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
from app.domains.content.models import Concept
from app.domains.catalog.models import SkillCatalog
from app.domains.assessment.models import (
    QuestionBank,
    Question,
    QuestionVersion,
    QuestionOption,
    QuestionConcept,
    QuestionSkill,
    CodingConfiguration,
    CodingTestCase,
    Assessment,
    AssessmentVersion,
    AssessmentAttempt,
    AssessmentResult,
    ConceptEvidence,
    SkillEvidence,
)
from app.domains.assessment.evaluators.coding import (
    set_code_execution_provider,
    MockSandboxProvider,
    UnavailableCodeExecutionProvider,
)
from app.core.security import UserRole, create_access_token


def make_user(email: str, role: UserRole, first_name: str, last_name: str, institution_id: str | None = None) -> User:
    return User(
        email=email,
        normalized_email=email.strip().lower(),
        hashed_password="hash",
        first_name=first_name,
        last_name=last_name,
        display_name=f"{first_name} {last_name}",
        role=role,
        institution_id=institution_id,
        is_active=True,
    )


@pytest.mark.asyncio
async def test_question_bank_and_question_authoring(db_session: AsyncSession, async_client: AsyncClient):
    """Verifies question bank creation, question versioning, and institutional isolation."""
    # 1. Setup institution and instructors
    inst1 = Institution(name="Tech Institute Alpha", code="TIA_DOM5")
    inst2 = Institution(name="Tech Institute Beta", code="TIB_DOM5")
    db_session.add_all([inst1, inst2])
    await db_session.flush()

    teacher1 = make_user("prof.alpha@example.com", UserRole.TEACHER, "Alpha", "Prof", inst1.id)
    teacher2 = make_user("prof.beta@example.com", UserRole.TEACHER, "Beta", "Prof", inst2.id)
    db_session.add_all([teacher1, teacher2])
    await db_session.commit()

    token1 = create_access_token(subject=teacher1.id, role=UserRole(teacher1.role), institution_id=inst1.id)
    token2 = create_access_token(subject=teacher2.id, role=UserRole(teacher2.role), institution_id=inst2.id)

    client = async_client
    # Create Question Bank in Inst1
    resp = await client.post(
        "/api/v1/question-banks",
        headers={"Authorization": f"Bearer {token1}"},
        json={"title": "Data Structures Bank", "description": "Core algorithms and structures", "visibility": "institution"},
    )
    assert resp.status_code == 201
    bank_data = resp.json()
    bank_id = bank_data["id"]
    assert bank_data["institution_id"] == inst1.id

    # Instructor from Inst2 cannot access Inst1's private question bank
    cross_resp = await client.get(
        f"/api/v1/question-banks/{bank_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert cross_resp.status_code == 404

    # Create Concept and Skill to map
    concept = Concept(name="Binary Search", slug="binary-search-dom5", difficulty="medium", status="approved")
    skill = SkillCatalog(name="Algorithms", code="ALG_DOM5", slug="algorithms-dom5", category="technical", status="approved")
    db_session.add_all([concept, skill])
    await db_session.commit()

    # Create Question with Version 1 (Single Choice)
    q_resp = await client.post(
        f"/api/v1/question-banks/{bank_id}/questions",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "question_type": "single_choice",
            "title": "Time Complexity of Binary Search",
            "prompt": "What is the worst-case time complexity of binary search on a sorted array of size N?",
            "difficulty": "medium",
            "points": 2.0,
            "negative_marks": 0.5,
            "options": [
                {"option_text": "O(N)", "order_index": 0, "is_correct": False},
                {"option_text": "O(log N)", "order_index": 1, "is_correct": True, "explanation": "Halves the search space each step"},
                {"option_text": "O(1)", "order_index": 2, "is_correct": False},
                {"option_text": "O(N^2)", "order_index": 3, "is_correct": False},
            ],
            "concepts": [{"concept_id": concept.id, "importance": 1.0, "is_primary": True, "weight": 1.0}],
            "skills": [{"skill_id": skill.id, "weight": 1.0}],
        },
    )
    assert q_resp.status_code == 201
    q_data = q_resp.json()
    assert q_data["current_version"] == 1
    q_id = q_data["id"]
    assert len(q_data["versions"]) == 1
    assert len(q_data["versions"][0]["options"]) == 4

    # Approve Question
    appr_resp = await client.patch(
        f"/api/v1/questions/{q_id}/status?new_status=approved",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert appr_resp.status_code == 200
    assert appr_resp.json()["status"] == "approved"

    # Create Question Version 2 without destroying Version 1
    v2_resp = await client.post(
        f"/api/v1/questions/{q_id}/versions",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "question_type": "single_choice",
            "title": "Time Complexity of Binary Search (Updated)",
            "prompt": "What is the tight worst-case time complexity of binary search?",
            "difficulty": "medium",
            "points": 2.5,
            "negative_marks": 0.5,
            "options": [
                {"option_text": "Theta(N)", "order_index": 0, "is_correct": False},
                {"option_text": "Theta(log N)", "order_index": 1, "is_correct": True},
                {"option_text": "Theta(1)", "order_index": 2, "is_correct": False},
            ],
            "concepts": [{"concept_id": concept.id, "importance": 1.0, "is_primary": True, "weight": 1.0}],
            "skills": [{"skill_id": skill.id, "weight": 1.0}],
        },
    )
    assert v2_resp.status_code == 201
    assert v2_resp.json()["version_number"] == 2

    # Check full question history has both versions intact
    q_detail_resp = await client.get(
        f"/api/v1/questions/{q_id}",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert q_detail_resp.status_code == 200
    hist_data = q_detail_resp.json()
    assert hist_data["current_version"] == 2
    assert len(hist_data["versions"]) == 2


@pytest.mark.asyncio
async def test_assessment_attempt_lifecycle_and_objective_scoring(db_session: AsyncSession, async_client: AsyncClient):
    """Tests assessment publishing, enrollment gating, question delivery sanitization, and deterministic scoring."""
    # 1. Setup Academic hierarchy & offering
    inst = Institution(name="National Tech", code="NT_DOM5")
    db_session.add(inst)
    await db_session.flush()

    dept = Department(institution_id=inst.id, name="Computer Science", code="CS_DOM5")
    db_session.add(dept)
    await db_session.flush()

    prog = Program(department_id=dept.id, name="B.Tech CS", code="BTCS_DOM5", degree_type="Bachelor")
    ay = AcademicYear(institution_id=inst.id, name="2026-2027", start_date=date(2026, 7, 1), end_date=date(2027, 6, 30))
    db_session.add_all([prog, ay])
    await db_session.flush()

    batch = Batch(institution_id=inst.id, program_id=prog.id, admission_year=2026, graduation_year=2030, label="2026-2030")
    sem = Semester(academic_year_id=ay.id, semester_number=1, label="Fall 2026", start_date=date(2026, 7, 1), end_date=date(2026, 12, 31))
    course = Course(institution_id=inst.id, department_id=dept.id, code="CS201_DOM5", title="Algorithms")
    db_session.add_all([batch, sem, course])
    await db_session.flush()

    section = Section(batch_id=batch.id, name="Sec-A", capacity=60)
    db_session.add(section)
    await db_session.flush()

    offering = CourseOffering(course_id=course.id, academic_year_id=ay.id, semester_id=sem.id, section_id=section.id)
    db_session.add(offering)
    await db_session.flush()

    teacher = make_user("prof.algo@example.com", UserRole.TEACHER, "Alan", "Turing", inst.id)
    student1 = make_user("stud1@example.com", UserRole.STUDENT, "Ada", "Lovelace", inst.id)
    student2_unenrolled = make_user("stud2@example.com", UserRole.STUDENT, "Grace", "Hopper", inst.id)
    db_session.add_all([teacher, student1, student2_unenrolled])
    await db_session.flush()

    prof1 = StudentAcademicProfile(user_id=student1.id, institution_id=inst.id, program_id=prog.id, batch_id=batch.id, enrollment_number="STU_001_D5", admission_year=2026, graduation_year=2030)
    prof2 = StudentAcademicProfile(user_id=student2_unenrolled.id, institution_id=inst.id, program_id=prog.id, batch_id=batch.id, enrollment_number="STU_002_D5", admission_year=2026, graduation_year=2030)
    db_session.add_all([prof1, prof2])
    await db_session.flush()

    enr1 = StudentEnrollment(student_profile_id=prof1.id, course_offering_id=offering.id, enrollment_status="enrolled")
    db_session.add(enr1)
    await db_session.flush()

    concept = Concept(name="Recursion", slug="recursion-dom5", difficulty="easy", status="approved")
    skill = SkillCatalog(name="Problem Solving", code="PS_DOM5", slug="problem-solving-dom5", category="technical", status="approved")
    db_session.add_all([concept, skill])
    await db_session.flush()

    # 2. Create Question Bank and Multiple Questions
    bank = QuestionBank(institution_id=inst.id, owner_id=teacher.id, title="Algo Quiz Bank", status="active")
    db_session.add(bank)
    await db_session.flush()

    # Q1: Single choice (Points: 5.0, Neg: 1.0)
    q1 = Question(bank_id=bank.id, question_type="single_choice", title="Base Case", difficulty="easy", status="approved", author_id=teacher.id)
    db_session.add(q1)
    await db_session.flush()
    qv1 = QuestionVersion(question_id=q1.id, version_number=1, prompt="What happens if recursion lacks a base case?", points=Decimal("5.00"), negative_marks=Decimal("1.00"), created_by=teacher.id)
    db_session.add(qv1)
    await db_session.flush()
    opt1_a = QuestionOption(question_version_id=qv1.id, option_text="Stack Overflow", order_index=0, is_correct=True, explanation="Unbounded call stack")
    opt1_b = QuestionOption(question_version_id=qv1.id, option_text="Runs instantly", order_index=1, is_correct=False)
    db_session.add_all([opt1_a, opt1_b])
    db_session.add(QuestionConcept(question_version_id=qv1.id, concept_id=concept.id, importance=1.0, is_primary=True))
    db_session.add(QuestionSkill(question_version_id=qv1.id, skill_id=skill.id, weight=Decimal("1.00")))

    # Q2: Numeric (Points: 5.0)
    q2 = Question(bank_id=bank.id, question_type="numeric", title="Fibonacci value", difficulty="easy", status="approved", author_id=teacher.id)
    db_session.add(q2)
    await db_session.flush()
    qv2 = QuestionVersion(question_id=q2.id, version_number=1, prompt="What is fib(6) where fib(0)=0, fib(1)=1?", points=Decimal("5.00"), negative_marks=Decimal("0.00"), evaluation_config={"tolerance": "0.0"}, created_by=teacher.id)
    db_session.add(qv2)
    await db_session.flush()
    # expected_value = 8
    qv2.evaluation_config = {"tolerance": "0.0", "expected_value": "8"}

    # Q3: Multiple choice with partial credit (Points: 10.0)
    q3 = Question(bank_id=bank.id, question_type="multiple_choice", title="Divide and Conquer", difficulty="medium", status="approved", author_id=teacher.id)
    db_session.add(q3)
    await db_session.flush()
    qv3 = QuestionVersion(question_id=q3.id, version_number=1, prompt="Select Divide & Conquer algorithms:", points=Decimal("10.00"), negative_marks=Decimal("0.00"), evaluation_config={"scoring_mode": "partial_credit"}, created_by=teacher.id)
    db_session.add(qv3)
    await db_session.flush()
    opt3_a = QuestionOption(question_version_id=qv3.id, option_text="Merge Sort", order_index=0, is_correct=True)
    opt3_b = QuestionOption(question_version_id=qv3.id, option_text="Quick Sort", order_index=1, is_correct=True)
    opt3_c = QuestionOption(question_version_id=qv3.id, option_text="Bubble Sort", order_index=2, is_correct=False)
    db_session.add_all([opt3_a, opt3_b, opt3_c])
    await db_session.commit()

    teacher_token = create_access_token(subject=teacher.id, role=UserRole(teacher.role), institution_id=inst.id)
    stud1_token = create_access_token(subject=student1.id, role=UserRole(student1.role), institution_id=inst.id)
    stud2_token = create_access_token(subject=student2_unenrolled.id, role=UserRole(student2_unenrolled.role), institution_id=inst.id)

    client = async_client
    # Teacher creates assessment for offering
    ass_resp = await client.post(
        "/api/v1/assessments",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={
            "course_offering_id": offering.id,
            "title": "Recursion & Algorithms Quiz",
            "instructions": "Answer all questions. Strict time limit.",
            "assessment_type": "quiz",
            "duration_minutes": 30,
            "passing_marks": 10.0,
            "attempts_allowed": 1,
            "feedback_policy": "after_submission",
        },
    )
    assert ass_resp.status_code == 201
    ass_id = ass_resp.json()["id"]

    # Publish assessment with chosen questions (Total: 5 + 5 + 10 = 20 marks)
    pub_resp = await client.post(
        f"/api/v1/assessments/{ass_id}/publish",
        headers={"Authorization": f"Bearer {teacher_token}"},
        params={"question_version_ids": [qv1.id, qv2.id, qv3.id]},
    )
    assert pub_resp.status_code == 201
    ass_ver = pub_resp.json()
    assert Decimal(str(ass_ver["total_marks"])) == Decimal("20.00")
    assert len(ass_ver["assessment_questions"]) == 3

    # Unenrolled student (student2) cannot start attempt
    unenr_resp = await client.post(
        f"/api/v1/assessments/{ass_id}/attempts",
        headers={"Authorization": f"Bearer {stud2_token}"},
    )
    assert unenr_resp.status_code == 403

    # Enrolled student (student1) starts attempt
    att_resp = await client.post(
        f"/api/v1/assessments/{ass_id}/attempts",
        headers={"Authorization": f"Bearer {stud1_token}"},
    )
    assert att_resp.status_code == 201
    att_data = att_resp.json()
    att_id = att_data["attempt_id"]
    assert att_data["status"] == "in_progress"

    # Student fetches questions: VERIFY answer keys are NOT leaked!
    delivery_resp = await client.get(
        f"/api/v1/attempts/{att_id}",
        headers={"Authorization": f"Bearer {stud1_token}"},
    )
    assert delivery_resp.status_code == 200
    del_data = delivery_resp.json()
    assert len(del_data["questions"]) == 3
    # Strict security check: ensure "is_correct" and "explanation" are completely absent from delivery options
    for q in del_data["questions"]:
        for opt in q["options"]:
            assert "is_correct" not in opt
            assert "explanation" not in opt

    # Student autosaves answers:
    # Q1: Stack Overflow (Correct -> +5.0)
    await client.post(
        f"/api/v1/attempts/{att_id}/autosave",
        headers={"Authorization": f"Bearer {stud1_token}"},
        json={"question_version_id": qv1.id, "response_type": "single_choice", "response_payload": {"selected_option_id": opt1_a.id}},
    )

    # Q2: 8 (Correct -> +5.0)
    await client.post(
        f"/api/v1/attempts/{att_id}/autosave",
        headers={"Authorization": f"Bearer {stud1_token}"},
        json={"question_version_id": qv2.id, "response_type": "numeric", "response_payload": {"value": "8"}},
    )

    # Q3: Merge Sort only (1 of 2 correct selected -> 50% partial credit -> +5.0 of 10.0)
    await client.post(
        f"/api/v1/attempts/{att_id}/autosave",
        headers={"Authorization": f"Bearer {stud1_token}"},
        json={"question_version_id": qv3.id, "response_type": "multiple_choice", "response_payload": {"selected_option_ids": [opt3_a.id]}},
    )

    # Submit attempt
    sub_resp = await client.post(
        f"/api/v1/attempts/{att_id}/submit",
        headers={"Authorization": f"Bearer {stud1_token}"},
    )
    assert sub_resp.status_code == 200
    assert sub_resp.json()["status"] == "submitted"

    # Student fetches result (feedback_policy is after_submission):
    # Total: 5.0 + 5.0 + 5.0 = 15.0 / 20.0 = 75.0% -> Passing!
    res_resp = await client.get(
        f"/api/v1/attempts/{att_id}/result",
        headers={"Authorization": f"Bearer {stud1_token}"},
    )
    assert res_resp.status_code == 200
    res_data = res_resp.json()
    assert Decimal(str(res_data["total_marks_obtained"])) == Decimal("15.00")
    assert Decimal(str(res_data["percentage"])) == Decimal("75.00")
    assert res_data["is_passed"] is True
    assert res_data["grade"] == "B"

    # Check Concept and Skill Evidence was generated with complete provenance
    ce_resp = await client.get(
        "/api/v1/students/me/evidence/concepts",
        headers={"Authorization": f"Bearer {stud1_token}"},
    )
    assert ce_resp.status_code == 200
    ce_list = ce_resp.json()
    assert len(ce_list) >= 1
    assert ce_list[0]["concept_id"] == concept.id
    assert Decimal(str(ce_list[0]["score"])) == Decimal("1.0000")  # 5/5 on Q1

    se_resp = await client.get(
        "/api/v1/students/me/evidence/skills",
        headers={"Authorization": f"Bearer {stud1_token}"},
    )
    assert se_resp.status_code == 200
    se_list = se_resp.json()
    assert len(se_list) >= 1
    assert se_list[0]["skill_id"] == skill.id


@pytest.mark.asyncio
async def test_manual_grading_rubric_workflow_and_coding_sandbox(db_session: AsyncSession, async_client: AsyncClient):
    """Tests manual faculty evaluation with rubrics, regrading, and safe coding sandbox evaluation."""
    inst = Institution(name="Global Engineering College", code="GEC_DOM5")
    db_session.add(inst)
    await db_session.flush()

    dept = Department(institution_id=inst.id, name="Software Eng", code="SE_DOM5")
    db_session.add(dept)
    await db_session.flush()

    prog = Program(department_id=dept.id, name="B.Tech SE", code="BTSE_DOM5", degree_type="Bachelor")
    ay = AcademicYear(institution_id=inst.id, name="2026-2027", start_date=date(2026, 7, 1), end_date=date(2027, 6, 30))
    db_session.add_all([prog, ay])
    await db_session.flush()

    batch = Batch(institution_id=inst.id, program_id=prog.id, admission_year=2026, graduation_year=2030, label="2026-2030")
    sem = Semester(academic_year_id=ay.id, semester_number=2, label="Spring 2027", start_date=date(2027, 1, 1), end_date=date(2027, 6, 30))
    course = Course(institution_id=inst.id, department_id=dept.id, code="SE301_DOM5", title="System Architecture")
    db_session.add_all([batch, sem, course])
    await db_session.flush()

    section = Section(batch_id=batch.id, name="Sec-SE", capacity=60)
    db_session.add(section)
    await db_session.flush()

    offering = CourseOffering(course_id=course.id, academic_year_id=ay.id, semester_id=sem.id, section_id=section.id)
    db_session.add(offering)
    await db_session.flush()

    teacher = make_user("lead.eval@example.com", UserRole.TEACHER, "Barbara", "Liskov", inst.id)
    student = make_user("candidate@example.com", UserRole.STUDENT, "Ken", "Thompson", inst.id)
    db_session.add_all([teacher, student])
    await db_session.flush()

    prof = StudentAcademicProfile(user_id=student.id, institution_id=inst.id, program_id=prog.id, batch_id=batch.id, enrollment_number="CAND_001_D5", admission_year=2026, graduation_year=2030)
    db_session.add(prof)
    await db_session.flush()

    enr = StudentEnrollment(student_profile_id=prof.id, course_offering_id=offering.id, enrollment_status="enrolled")
    db_session.add(enr)
    await db_session.commit()

    teacher_token = create_access_token(subject=teacher.id, role=UserRole(teacher.role), institution_id=inst.id)
    stud_token = create_access_token(subject=student.id, role=UserRole(student.role), institution_id=inst.id)

    client = async_client
    # Create Evaluation Rubric
    rub_resp = await client.post(
        "/api/v1/rubrics",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={
            "title": "Architecture Essay Rubric",
            "criteria": [
                {"title": "Clarity & Cohesion", "max_points": 5.0, "weight": 1.0, "order_index": 0},
                {"title": "Technical Depth", "max_points": 5.0, "weight": 1.0, "order_index": 1},
            ],
        },
    )
    assert rub_resp.status_code == 201
    rub_id = rub_resp.json()["id"]

    # Create Question Bank & Subjective Question
    bank = QuestionBank(institution_id=inst.id, owner_id=teacher.id, title="Architecture Bank")
    db_session.add(bank)
    await db_session.flush()

    # Subjective Question (10 points)
    q_subj = Question(bank_id=bank.id, question_type="short_answer", title="Explain Microservices", difficulty="hard", status="approved", author_id=teacher.id)
    db_session.add(q_subj)
    await db_session.flush()
    qv_subj = QuestionVersion(question_id=q_subj.id, version_number=1, prompt="Discuss tradeoffs of microservices vs monoliths.", points=Decimal("10.00"), rubric_id=rub_id, created_by=teacher.id)
    db_session.add(qv_subj)

    # Coding Question (10 points)
    q_code = Question(bank_id=bank.id, question_type="coding", title="Reverse Array", difficulty="easy", status="approved", author_id=teacher.id)
    db_session.add(q_code)
    await db_session.flush()
    qv_code = QuestionVersion(question_id=q_code.id, version_number=1, prompt="Write a function to reverse a list in-place.", points=Decimal("10.00"), created_by=teacher.id)
    db_session.add(qv_code)
    await db_session.flush()

    cc = CodingConfiguration(
        question_version_id=qv_code.id,
        language="python",
        starter_code="def reverse_array(arr):\n    pass",
        time_limit_ms=1000,
        memory_limit_mb=128,
    )
    db_session.add(cc)
    await db_session.flush()
    tc_pub = CodingTestCase(coding_config_id=cc.id, input_data="[1, 2, 3]", expected_output="[3, 2, 1]", is_hidden=False)
    tc_hid = CodingTestCase(coding_config_id=cc.id, input_data="[5, 4, 3, 2, 1]", expected_output="[1, 2, 3, 4, 5]", is_hidden=True)
    db_session.add_all([tc_pub, tc_hid])
    await db_session.commit()

    # Teacher publishes assessment with subjective + coding questions
    ass_resp = await client.post(
        "/api/v1/assessments",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={
            "course_offering_id": offering.id,
            "title": "Midterm Architecture Exam",
            "assessment_type": "midterm",
            "duration_minutes": 60,
            "passing_marks": 10.0,
            "feedback_policy": "after_release",
        },
    )
    ass_id = ass_resp.json()["id"]
    await client.post(
        f"/api/v1/assessments/{ass_id}/publish",
        headers={"Authorization": f"Bearer {teacher_token}"},
        params={"question_version_ids": [qv_subj.id, qv_code.id]},
    )

    # Configure safe mock sandbox provider to simulate pass of test cases
    set_code_execution_provider(MockSandboxProvider(simulate_pass_rate=1.0))

    # Student starts and submits attempt
    att_resp = await client.post(
        f"/api/v1/assessments/{ass_id}/attempts",
        headers={"Authorization": f"Bearer {stud_token}"},
    )
    att_id = att_resp.json()["attempt_id"]

    # Verify question delivery hides the hidden test case!
    del_resp = await client.get(
        f"/api/v1/attempts/{att_id}",
        headers={"Authorization": f"Bearer {stud_token}"},
    )
    del_data = del_resp.json()
    coding_q = next(q for q in del_data["questions"] if q["question_type"] == "coding")
    assert len(coding_q["public_test_cases"]) == 1
    assert coding_q["public_test_cases"][0]["input_data"] == "[1, 2, 3]"

    # Autosave answers
    await client.post(
        f"/api/v1/attempts/{att_id}/autosave",
        headers={"Authorization": f"Bearer {stud_token}"},
        json={"question_version_id": qv_subj.id, "response_type": "short_answer", "response_payload": {"text_answer": "Microservices introduce network latency and distributed complexity but improve decoupled deployments."}},
    )
    await client.post(
        f"/api/v1/attempts/{att_id}/autosave",
        headers={"Authorization": f"Bearer {stud_token}"},
        json={"question_version_id": qv_code.id, "response_type": "coding", "response_payload": {"code": "def reverse_array(arr):\n    return arr[::-1]"}},
    )

    # Submit attempt
    sub_resp = await client.post(
        f"/api/v1/attempts/{att_id}/submit",
        headers={"Authorization": f"Bearer {stud_token}"},
    )
    assert sub_resp.status_code == 200
    # Result status is "draft" because manual evaluation is pending
    assert sub_resp.json()["result_status"] == "draft"

    # Student attempts to fetch result: FORBIDDEN because feedback_policy is "after_release" and status is draft
    gate_resp = await client.get(
        f"/api/v1/attempts/{att_id}/result",
        headers={"Authorization": f"Bearer {stud_token}"},
    )
    assert gate_resp.status_code == 403

    # Instructor grades the subjective question manually
    await db_session.rollback()
    att_db_stmt = select(AssessmentAttempt).where(AssessmentAttempt.id == att_id).options(selectinload(AssessmentAttempt.evaluations))
    att_db_res = await db_session.execute(att_db_stmt)
    att_db = att_db_res.scalar_one()
    manual_eval = next(e for e in att_db.evaluations if e.evaluation_type == "manual")

    grade_resp = await client.post(
        f"/api/v1/evaluations/{manual_eval.id}/grade",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={"awarded_marks": 8.5, "evaluator_notes": "Well articulated trade-offs, could mention saga patterns."},
    )
    assert grade_resp.status_code == 200
    assert Decimal(str(grade_resp.json()["awarded_marks"])) == Decimal("8.50")

    # Instructor releases the result
    rel_resp = await client.post(
        f"/api/v1/results/{att_id}/release",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert rel_resp.status_code == 200
    assert rel_resp.json()["status"] == "released"

    # Now student can view their released result:
    # Coding: 10/10 (MockSandbox passed all tests) + Manual: 8.5/10 = 18.5/20 = 92.5% -> A+
    student_res = await client.get(
        f"/api/v1/attempts/{att_id}/result",
        headers={"Authorization": f"Bearer {stud_token}"},
    )
    assert student_res.status_code == 200
    res_data = student_res.json()
    assert Decimal(str(res_data["total_marks_obtained"])) == Decimal("18.50")
    assert Decimal(str(res_data["percentage"])) == Decimal("92.50")
    assert res_data["grade"] == "A+"
    assert res_data["is_passed"] is True

    # Reset provider back to unavailable
    set_code_execution_provider(UnavailableCodeExecutionProvider())
