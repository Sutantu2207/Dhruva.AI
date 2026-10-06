"""Domain 9 — Institutional Analytics, Faculty Grading Workflows & Departmental Intelligence Tests."""

import pytest
import uuid
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import UserRole, get_password_hash
from app.domains.identity.models import User
from app.domains.academic.models import (
    Institution,
    Department,
    Program,
    Batch,
    Section,
    AcademicYear,
    Semester,
    Course,
    CourseOffering,
    StudentAcademicProfile,
    TeacherAcademicProfile,
    TeachingAssignment,
    StudentEnrollment,
)
from app.domains.assessment.models import (
    Assessment,
    AssessmentVersion,
    AssessmentAttempt,
    AssessmentEvaluation,
)
from app.domains.profiles.models import (
    StudentProject,
)
from app.domains.project_intelligence.models import (
    ProjectEvidence,
)
from app.domains.institutional_intelligence.models import (
    AcademicInterventionSignal,
    EvaluationRegradeAudit,
)
from app.domains.institutional_intelligence.intervention_engine import InterventionSignalEngine
from app.domains.institutional_intelligence.course_analytics_engine import CourseAnalyticsEngine
from app.domains.institutional_intelligence.department_analytics_engine import DepartmentAnalyticsEngine
from app.domains.institutional_intelligence.placement_analytics_engine import PlacementAnalyticsEngine


# =========================================================================
# 1. PURE ENGINE UNIT TESTS
# =========================================================================

def test_pure_intervention_signal_engine_conditions():
    """Verify deterministic detection of academic distress without psychologizing."""
    # Scenario A: Healthy student -> 0 signals
    healthy_signals = InterventionSignalEngine.evaluate_student_signals(
        assessment_attempts=[
            {"id": "a1", "status": "evaluated", "percentage": 85.0, "is_passed": True},
            {"id": "a2", "status": "evaluated", "percentage": 90.0, "is_passed": True},
        ],
        concept_states=[
            {"concept_id": "c1", "mastery_score": 0.82},
            {"concept_id": "c2", "mastery_score": 0.75},
        ],
        overdue_reviews=[],
        lesson_progress=[{"completion_percentage": 95.0}],
        prerequisite_checks=[],
        project_skills=[{"claimed_level": "proficient", "verification_status": "verified"}],
        days_since_last_activity=2,
    )
    assert len(healthy_signals) == 0

    # Scenario B: High distress student -> Multiple observable signals
    distressed_signals = InterventionSignalEngine.evaluate_student_signals(
        assessment_attempts=[
            {"id": "a1", "status": "evaluated", "percentage": 40.0, "is_passed": False},
            {"id": "a2", "status": "evaluated", "percentage": 35.0, "is_passed": False},
            {"id": "a3", "status": "evaluated", "percentage": 42.0, "is_passed": False},
        ],
        concept_states=[
            {"concept_id": "c1", "mastery_score": 0.20},
            {"concept_id": "c2", "mastery_score": 0.25},
            {"concept_id": "c3", "mastery_score": 0.30},
        ],
        overdue_reviews=[
            {"concept_id": "c1", "days_overdue": 6},
            {"concept_id": "c2", "days_overdue": 8},
            {"concept_id": "c3", "days_overdue": 7},
        ],
        lesson_progress=[
            {"completion_percentage": 10.0},
            {"completion_percentage": 15.0},
            {"completion_percentage": 20.0},
            {"completion_percentage": 12.0},
        ],
        prerequisite_checks=[
            {"is_ready": False, "prerequisite_concept_id": "p1"},
        ],
        project_skills=[
            {"claimed_level": "advanced", "verification_status": "unverified"},
            {"claimed_level": "advanced", "verification_status": "unverified"},
            {"claimed_level": "expert", "verification_status": "unverified"},
            {"claimed_level": "proficient", "verification_status": "unverified"},
        ],
        days_since_last_activity=16,
    )

    signal_types = [s["signal_type"] for s in distressed_signals]
    assert "repeated_assessment_failures" in signal_types
    assert "persistent_low_concept_mastery" in signal_types
    assert "overdue_reviews" in signal_types
    assert "incomplete_coursework" in signal_types
    assert "weak_prerequisite_mastery" in signal_types
    assert "insufficient_evidence" in signal_types
    assert "prolonged_inactivity" in signal_types

    # Verify severity and deterministic actionable recommendation
    failure_signal = next(s for s in distressed_signals if s["signal_type"] == "repeated_assessment_failures")
    assert failure_signal["severity"] == "urgent"
    assert "diagnostic assessment" in failure_signal["recommended_action"].lower()


def test_pure_course_and_assessment_analytics_engine():
    """Verify course assessment score distributions and question difficulty detection."""
    metric = CourseAnalyticsEngine.compute_assessment_metrics(
        assessment_id="ass-1",
        title="Midterm Examination",
        enrolled_count=20,
        attempts=[
            {"id": "att-1", "status": "evaluated", "percentage": 88.0, "is_passed": True},
            {"id": "att-2", "status": "evaluated", "percentage": 72.0, "is_passed": True},
            {"id": "att-3", "status": "evaluated", "percentage": 45.0, "is_passed": False},
            {"id": "att-4", "status": "evaluated", "percentage": 94.0, "is_passed": True},
        ],
        questions_raw=[
            {"id": "q1", "version_id": "qv1", "title": "Easy Question"},
            {"id": "q2", "version_id": "qv2", "title": "Difficult Question"},
        ],
        responses=[
            {"question_id": "q1", "is_correct": True, "response_payload": {"ans": "A"}, "awarded_marks": 5.0},
            {"question_id": "q1", "is_correct": True, "response_payload": {"ans": "A"}, "awarded_marks": 5.0},
            {"question_id": "q2", "is_correct": False, "response_payload": {"ans": "B"}, "awarded_marks": 0.0},
            {"question_id": "q2", "is_correct": False, "response_payload": {}, "awarded_marks": 0.0},
        ],
    )

    assert metric["total_assigned"] == 20
    assert metric["total_completed"] == 4
    assert metric["completion_rate"] == 0.20
    assert metric["average_score"] == 74.75
    assert metric["pass_rate"] == 0.75
    assert metric["score_distribution"]["85_to_100"] == 2
    assert metric["score_distribution"]["0_to_49"] == 1

    q2_metric = next(q for q in metric["questions"] if q["question_id"] == "q2")
    assert q2_metric["accuracy_rate"] == 0.0
    assert q2_metric["skip_rate"] == 0.50
    assert q2_metric["review_recommended"] is True


def test_pure_department_comparison_privacy_suppression():
    """Verify small cohorts (< 3 students) are strictly suppressed in aggregate views."""
    departments = [
        {
            "department_id": "dept-cs",
            "department_name": "Computer Science",
            "department_code": "CSE",
            "total_students": 45,
            "average_course_completion": 0.85,
            "average_assessment_score": 78.5,
            "concept_mastery_average": 0.76,
            "career_readiness_average": 0.72,
            "active_intervention_signals_count": 4,
        },
        {
            "department_id": "dept-mining",
            "department_name": "Mining Engineering",
            "department_code": "MIN",
            "total_students": 2,  # Cohort size below threshold of 3
            "average_course_completion": 0.95,
            "average_assessment_score": 92.0,
            "concept_mastery_average": 0.88,
            "career_readiness_average": 0.85,
            "active_intervention_signals_count": 0,
        },
    ]

    comparisons = DepartmentAnalyticsEngine.compare_departments(
        department_summaries=departments,
        min_cohort_size=3,
    )

    cs_comp = next(c for c in comparisons if c["department_id"] == "dept-cs")
    assert cs_comp["is_suppressed"] is False
    assert cs_comp["average_score"] == 78.5
    assert cs_comp["completion_rate"] == 0.85

    min_comp = next(c for c in comparisons if c["department_id"] == "dept-mining")
    assert min_comp["is_suppressed"] is True
    assert min_comp["student_count"] == 2
    # Sensitive aggregates must be masked to None
    assert min_comp["average_score"] is None
    assert min_comp["completion_rate"] is None
    assert min_comp["concept_mastery"] is None
    assert min_comp["career_readiness"] is None


def test_pure_placement_analytics_engine():
    """Verify honest employability synthesis without fabricated predictions."""
    result = PlacementAnalyticsEngine.aggregate_placement_intelligence(
        total_students=10,
        career_goals=[
            {"career_title": "Full Stack Developer"},
            {"career_title": "Full Stack Developer"},
            {"career_title": "Cloud Architect"},
        ],
        career_readiness_states=[
            {"overall_readiness_percentage": 82.0},
            {"overall_readiness_percentage": 65.0},
            {"overall_readiness_percentage": 40.0},
        ],
        placement_states=[
            {"readiness_tier": "ready"},
            {"readiness_tier": "near_ready"},
        ],
        student_verified_projects={"s1": 2, "s2": 1, "s3": 0},
        portfolio_snapshots=[{"overall_health_score": 75.0}],
        skill_gaps=[
            {"skill_name": "Docker"},
            {"skill_name": "Docker"},
            {"skill_name": "Kubernetes"},
        ],
    )

    assert result["evaluated_students_count"] == 3
    assert result["average_career_readiness"] == 62.33
    assert result["career_readiness_tiers"]["ready"] == 1
    assert result["career_readiness_tiers"]["near_ready"] == 1
    assert result["career_readiness_tiers"]["developing"] == 1
    assert result["career_readiness_tiers"]["unassessed"] == 7
    assert result["verified_project_coverage_rate"] == 0.20  # 2 students / 10 total
    assert result["portfolio_health_average"] == 75.0
    assert result["top_systemic_skill_gaps"][0]["skill_name"] == "Docker"
    assert result["top_systemic_skill_gaps"][0]["impacted_students_count"] == 2


# =========================================================================
# 2. INTEGRATION TESTS FOR WORKFLOWS, RBAC, GRADING & SIGNALS
# =========================================================================

@pytest.mark.asyncio
async def test_faculty_dashboard_and_course_analytics_workflow(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    """Test teacher dashboard scoping, course offering drill-down, and CSV export."""
    # 1. Setup institution, department, course, offering, teacher, and student
    u_suff = uuid.uuid4().hex[:6]
    inst = Institution(name=f"Inst D9 {u_suff}", code=f"I9_{u_suff}")
    db_session.add(inst)
    await db_session.flush()

    dept = Department(institution_id=inst.id, name=f"Dept D9 {u_suff}", code=f"D9_{u_suff}")
    db_session.add(dept)
    await db_session.flush()

    prog = Program(department_id=dept.id, name="B.Tech CS", code=f"P_{u_suff}", degree_type="B.Tech")
    db_session.add(prog)
    await db_session.flush()

    batch = Batch(institution_id=inst.id, program_id=prog.id, label="2022-2026", admission_year=2022, graduation_year=2026)
    ay = AcademicYear(institution_id=inst.id, name=f"2025-2026_{u_suff}", start_date=datetime.now(timezone.utc).date(), end_date=datetime.now(timezone.utc).date())
    db_session.add_all([batch, ay])
    await db_session.flush()

    sem = Semester(academic_year_id=ay.id, semester_number=6, label="Sem 6", start_date=datetime.now(timezone.utc).date(), end_date=datetime.now(timezone.utc).date())
    sec = Section(batch_id=batch.id, name="A")
    course = Course(institution_id=inst.id, department_id=dept.id, code=f"CS90_{u_suff}", title="Distributed Systems")
    db_session.add_all([sem, sec, course])
    await db_session.flush()

    offering = CourseOffering(
        course_id=course.id,
        academic_year_id=ay.id,
        semester_id=sem.id,
        section_id=sec.id,
    )
    db_session.add(offering)
    await db_session.flush()

    # Teacher user
    t_user = User(
        email=f"prof_{u_suff}@univ.edu",
        normalized_email=f"prof_{u_suff}@univ.edu",
        hashed_password=get_password_hash("ProfPass123!"),
        role=UserRole.TEACHER,
        first_name="Alan",
        last_name="Turing",
        display_name="Prof. Turing",
        institution_id=inst.id,
    )
    # Student user
    s_user = User(
        email=f"stud_{u_suff}@univ.edu",
        normalized_email=f"stud_{u_suff}@univ.edu",
        hashed_password=get_password_hash("StudentPass123!"),
        role=UserRole.STUDENT,
        first_name="Ada",
        last_name="Lovelace",
        display_name="Ada Lovelace",
        institution_id=inst.id,
    )
    db_session.add_all([t_user, s_user])
    await db_session.flush()

    t_prof = TeacherAcademicProfile(
        user_id=t_user.id,
        institution_id=inst.id,
        department_id=dept.id,
        employee_id=f"EMP_{u_suff}",
    )
    s_prof = StudentAcademicProfile(
        user_id=s_user.id,
        institution_id=inst.id,
        program_id=prog.id,
        batch_id=batch.id,
        enrollment_number=f"ENR_{u_suff}",
        admission_year=2022,
        graduation_year=2026,
    )
    db_session.add_all([t_prof, s_prof])
    await db_session.flush()

    # Assign teacher to offering
    assign = TeachingAssignment(
        teacher_profile_id=t_prof.id,
        course_offering_id=offering.id,
        assignment_role="lead_instructor",
    )
    enroll = StudentEnrollment(
        student_profile_id=s_prof.id,
        course_offering_id=offering.id,
    )
    db_session.add_all([assign, enroll])
    await db_session.commit()

    # Login as Teacher
    from app.core.security import create_access_token
    token = create_access_token(t_user.id, UserRole.TEACHER)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. GET /faculty/dashboard-analytics
    dash_res = await async_client.get("/api/v1/faculty/dashboard-analytics", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["assigned_offerings_count"] == 1
    assert dash_data["total_enrolled_students"] == 1
    assert dash_data["offerings"][0]["offering_id"] == offering.id

    # 2. GET /faculty/courses/{offering_id}/analytics
    off_res = await async_client.get(f"/api/v1/faculty/courses/{offering.id}/analytics", headers=headers)
    assert off_res.status_code == 200
    off_data = off_res.json()
    assert off_data["offering_id"] == offering.id
    assert off_data["enrolled_count"] == 1
    assert off_data["algorithm_version"] == "v1.0.0-deterministic"

    # 3. GET /faculty/courses/{offering_id}/export (CSV)
    csv_res = await async_client.get(f"/api/v1/faculty/courses/{offering.id}/export", headers=headers)
    assert csv_res.status_code == 200
    assert csv_res.headers["content-type"].startswith("text/csv")
    assert "Distributed Systems" in csv_res.text


@pytest.mark.asyncio
async def test_grading_queue_manual_scoring_and_regrade_audit(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    """Test manual rubric evaluation grading and immutable score revision with audit trail."""
    u_suff = uuid.uuid4().hex[:6]
    inst = Institution(name=f"Inst GQ {u_suff}", code=f"IGQ_{u_suff}")
    db_session.add(inst)
    await db_session.flush()

    dept = Department(institution_id=inst.id, name=f"Dept GQ {u_suff}", code=f"DGQ_{u_suff}")
    db_session.add(dept)
    await db_session.flush()

    prog = Program(department_id=dept.id, name="B.Tech CS", code=f"PGQ_{u_suff}", degree_type="B.Tech")
    db_session.add(prog)
    await db_session.flush()

    batch = Batch(institution_id=inst.id, program_id=prog.id, label="2022-2026", admission_year=2022, graduation_year=2026)
    course = Course(institution_id=inst.id, department_id=dept.id, code=f"CSGQ_{u_suff}", title="Algorithms")
    db_session.add_all([batch, course])
    await db_session.flush()

    # Users
    t_user = User(
        email=f"evaluator_{u_suff}@univ.edu",
        normalized_email=f"evaluator_{u_suff}@univ.edu",
        hashed_password=get_password_hash("Pass123!"),
        role=UserRole.TEACHER,
        first_name="Grace",
        last_name="Hopper",
        display_name="Prof. Hopper",
        institution_id=inst.id,
    )
    s_user = User(
        email=f"candidate_{u_suff}@univ.edu",
        normalized_email=f"candidate_{u_suff}@univ.edu",
        hashed_password=get_password_hash("Pass123!"),
        role=UserRole.STUDENT,
        first_name="Claude",
        last_name="Shannon",
        display_name="Claude Shannon",
        institution_id=inst.id,
    )
    db_session.add_all([t_user, s_user])
    await db_session.flush()

    t_prof = TeacherAcademicProfile(user_id=t_user.id, institution_id=inst.id, department_id=dept.id, employee_id=f"T_{u_suff}")
    s_prof = StudentAcademicProfile(user_id=s_user.id, institution_id=inst.id, program_id=prog.id, batch_id=batch.id, enrollment_number=f"S_{u_suff}", admission_year=2022, graduation_year=2026)
    db_session.add_all([t_prof, s_prof])
    await db_session.flush()

    # Assessment Attempt with Manual Evaluation
    ass = Assessment(institution_id=inst.id, title="Algorithm Design Exam")
    db_session.add(ass)
    await db_session.flush()

    ass_v = AssessmentVersion(assessment_id=ass.id, version_number=1, title="v1", total_marks=Decimal("10.00"), passing_marks=Decimal("5.00"))
    db_session.add(ass_v)
    await db_session.flush()

    attempt = AssessmentAttempt(
        assessment_version_id=ass_v.id,
        student_profile_id=s_prof.id,
        started_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
        submitted_at=datetime.now(timezone.utc),
        status="under_evaluation",
    )
    db_session.add(attempt)
    await db_session.flush()

    eval_item = AssessmentEvaluation(
        attempt_id=attempt.id,
        question_version_id="qv-algorithm-proof",
        max_marks=Decimal("10.00"),
        awarded_marks=Decimal("0.00"),
        evaluation_type="manual",
    )
    db_session.add(eval_item)
    await db_session.commit()

    from app.core.security import create_access_token
    token = create_access_token(t_user.id, UserRole.TEACHER)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. GET /faculty/grading -> Inspect Queue
    g_res = await async_client.get("/api/v1/faculty/grading", headers=headers)
    assert g_res.status_code == 200
    queue = g_res.json()
    assert len(queue) >= 1
    manual_q = next(item for item in queue if item["item_id"] == eval_item.id)
    assert manual_q["item_type"] == "manual_question"
    assert manual_q["student_name"] == "Claude Shannon"

    # 2. POST /faculty/grading/questions/{evaluation_id} -> Award marks
    grade_res = await async_client.post(
        f"/api/v1/faculty/grading/questions/{eval_item.id}",
        json={"awarded_marks": "8.50", "feedback": "Solid proof structure with minor edge-case oversight."},
        headers=headers,
    )
    assert grade_res.status_code == 200
    grade_data = grade_res.json()
    assert grade_data["status"] == "graded"
    assert grade_data["awarded_marks"] == 8.50

    # 3. POST /faculty/grading/questions/{evaluation_id}/regrade -> Revision with rationale
    regrade_res = await async_client.post(
        f"/api/v1/faculty/grading/questions/{eval_item.id}/regrade",
        json={"new_marks": "9.00", "reason": "Re-reviewed edge case justification in student appendix."},
        headers=headers,
    )
    assert regrade_res.status_code == 200
    regrade_data = regrade_res.json()
    assert regrade_data["status"] == "regraded"
    assert regrade_data["previous_marks"] == 8.50
    assert regrade_data["new_marks"] == 9.00
    assert "appendix" in regrade_data["reason"]


@pytest.mark.asyncio
async def test_early_intervention_signals_lifecycle_and_conversion(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    """Test automatic detection, acknowledgement, and elevation of academic signals."""
    u_suff = uuid.uuid4().hex[:6]
    inst = Institution(name=f"Inst IS {u_suff}", code=f"IIS_{u_suff}")
    db_session.add(inst)
    await db_session.flush()

    dept = Department(institution_id=inst.id, name=f"Dept IS {u_suff}", code=f"DIS_{u_suff}")
    db_session.add(dept)
    await db_session.flush()

    prog = Program(department_id=dept.id, name="B.Tech CS", code=f"PIS_{u_suff}", degree_type="B.Tech")
    db_session.add(prog)
    await db_session.flush()

    batch = Batch(institution_id=inst.id, program_id=prog.id, label="2022-2026", admission_year=2022, graduation_year=2026)
    course = Course(institution_id=inst.id, department_id=dept.id, code=f"CSIS_{u_suff}", title="Databases")
    db_session.add_all([batch, course])
    await db_session.flush()

    t_user = User(email=f"teacher_is_{u_suff}@univ.edu", normalized_email=f"teacher_is_{u_suff}@univ.edu", hashed_password=get_password_hash("Pass123!"), role=UserRole.TEACHER, first_name="T", last_name="User", display_name="Teacher", institution_id=inst.id)
    s_user = User(email=f"student_is_{u_suff}@univ.edu", normalized_email=f"student_is_{u_suff}@univ.edu", hashed_password=get_password_hash("Pass123!"), role=UserRole.STUDENT, first_name="S", last_name="User", display_name="Student", institution_id=inst.id)
    db_session.add_all([t_user, s_user])
    await db_session.flush()

    s_prof = StudentAcademicProfile(user_id=s_user.id, institution_id=inst.id, program_id=prog.id, batch_id=batch.id, enrollment_number=f"ENR_IS_{u_suff}", admission_year=2022, graduation_year=2026)
    db_session.add(s_prof)
    await db_session.flush()

    # Create failed attempts to trigger deterministic signal engine
    ass = Assessment(institution_id=inst.id, title="DB Midterm")
    db_session.add(ass)
    await db_session.flush()
    ass_v = AssessmentVersion(assessment_id=ass.id, version_number=1, title="v1", total_marks=Decimal("100.00"), passing_marks=Decimal("50.00"))
    db_session.add(ass_v)
    await db_session.flush()

    for num in [1, 2]:
        att = AssessmentAttempt(
            assessment_version_id=ass_v.id,
            student_profile_id=s_prof.id,
            attempt_number=num,
            started_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            submitted_at=datetime.now(timezone.utc),
            status="evaluated",
            percentage=Decimal("38.00"),
            is_passed=False,
        )
        db_session.add(att)
    await db_session.commit()

    from app.core.security import create_access_token
    token = create_access_token(t_user.id, UserRole.TEACHER)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. POST /interventions/signals/scan
    scan_res = await async_client.post("/api/v1/interventions/signals/scan", headers=headers)
    assert scan_res.status_code == 200
    signals = scan_res.json()
    assert len(signals) >= 1
    sig = signals[0]
    assert sig["signal_type"] == "repeated_assessment_failures"
    assert sig["severity"] in ("high", "urgent")
    assert sig["status"] == "detected"

    # 2. POST /interventions/signals/{signal_id}/acknowledge
    ack_res = await async_client.post(
        f"/api/v1/interventions/signals/{sig['id']}/acknowledge",
        json={"notes": "Acknowledged by teacher, reviewing upcoming test."},
        headers=headers,
    )
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "acknowledged"

    # 3. POST /interventions/signals/{signal_id}/convert -> Elevate to StudentIntervention
    conv_res = await async_client.post(
        f"/api/v1/interventions/signals/{sig['id']}/convert",
        json={
            "category": "academic_support",
            "priority": "high",
            "action_plan": "Weekly 1-on-1 tutoring on relational schema normalization.",
        },
        headers=headers,
    )
    assert conv_res.status_code == 200
    conv_data = conv_res.json()
    assert conv_data["status"] == "intervention_created"
    assert conv_data["intervention_id"] is not None


@pytest.mark.asyncio
async def test_hod_scoping_isolation_and_department_comparisons(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    """Test HOD cross-department denial and Institutional Admin comparison."""
    u_suff = uuid.uuid4().hex[:6]
    inst = Institution(name=f"Inst HOD {u_suff}", code=f"IHOD_{u_suff}")
    db_session.add(inst)
    await db_session.flush()

    dept1 = Department(institution_id=inst.id, name=f"Computer Science {u_suff}", code=f"CSE_{u_suff}")
    dept2 = Department(institution_id=inst.id, name=f"Mechanical Eng {u_suff}", code=f"ME_{u_suff}")
    db_session.add_all([dept1, dept2])
    await db_session.flush()

    # HOD User of Dept 1
    hod_user = User(email=f"hod_cse_{u_suff}@univ.edu", normalized_email=f"hod_cse_{u_suff}@univ.edu", hashed_password=get_password_hash("Pass123!"), role=UserRole.HOD, first_name="HOD", last_name="CSE", display_name="Dr. CSE", institution_id=inst.id)
    # Admin User
    admin_user = User(email=f"admin_{u_suff}@univ.edu", normalized_email=f"admin_{u_suff}@univ.edu", hashed_password=get_password_hash("Pass123!"), role=UserRole.INSTITUTION_ADMIN, first_name="Dean", last_name="Admin", display_name="Dean Admin", institution_id=inst.id)
    # Student User
    stud_user = User(email=f"stud_{u_suff}@univ.edu", normalized_email=f"stud_{u_suff}@univ.edu", hashed_password=get_password_hash("Pass123!"), role=UserRole.STUDENT, first_name="S", last_name="U", display_name="Student", institution_id=inst.id)
    db_session.add_all([hod_user, admin_user, stud_user])
    await db_session.flush()

    hod_prof = TeacherAcademicProfile(user_id=hod_user.id, institution_id=inst.id, department_id=dept1.id, employee_id=f"HOD_{u_suff}")
    db_session.add(hod_prof)
    await db_session.commit()

    from app.core.security import create_access_token
    hod_token = create_access_token(hod_user.id, UserRole.HOD)
    admin_token = create_access_token(admin_user.id, UserRole.INSTITUTION_ADMIN)
    stud_token = create_access_token(stud_user.id, UserRole.STUDENT)

    # 1. HOD accesses own department -> 200 OK
    res_own = await async_client.get(
        f"/api/v1/hod/departments/{dept1.id}/analytics",
        headers={"Authorization": f"Bearer {hod_token}"},
    )
    assert res_own.status_code == 200
    assert res_own.json()["department_id"] == dept1.id

    # 2. HOD attempts cross-department access -> 403 Forbidden
    res_other = await async_client.get(
        f"/api/v1/hod/departments/{dept2.id}/analytics",
        headers={"Authorization": f"Bearer {hod_token}"},
    )
    assert res_other.status_code == 403
    assert "isolated" in res_other.json()["detail"].lower()

    # 3. Student attempts to access HOD analytics -> 403 Forbidden
    res_stud = await async_client.get(
        f"/api/v1/hod/departments/{dept1.id}/analytics",
        headers={"Authorization": f"Bearer {stud_token}"},
    )
    assert res_stud.status_code == 403

    # 4. Institution Admin compares departments -> 200 OK with privacy suppression
    res_comp = await async_client.get(
        "/api/v1/admin/departments/compare",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_comp.status_code == 200
    comp_data = res_comp.json()
    assert comp_data["minimum_cohort_size"] == 3
    assert len(comp_data["departments"]) >= 2
    # Both depts have 0 students in this test -> both suppressed
    for d in comp_data["departments"]:
        assert d["is_suppressed"] is True
        assert d["average_score"] is None
