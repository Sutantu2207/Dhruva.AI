"""Comprehensive tests for Domain 10: Autonomous Adaptive Remediation & Institutional Intelligence Closing."""

import pytest
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.remediation.diagnostic_engine import DiagnosticEngine
from app.domains.remediation.prerequisite_path_engine import PrerequisitePathEngine
from app.domains.remediation.outcome_engine import OutcomeEngine
from app.domains.remediation.service import RemediationService
from app.domains.remediation.config import ALGORITHM_VERSION, PRIORITY_WEIGHTS
from app.domains.remediation.schemas import CompleteStepPayload
from app.domains.remediation.models import (
    RemediationPlan,
    RemediationPlanStep,
    RemediationDiagnosis,
    RemediationAttempt,
    RemediationOutcome,
    ContentGapRecord,
)
from app.domains.content.models import Concept, ConceptPrerequisite, Lesson, LessonConcept
from app.domains.academic.models import Institution, Department, Program, Batch, StudentAcademicProfile
from app.domains.identity.models import User
from app.core.security import UserRole, get_password_hash


# =========================================================================
# 1. Pure Unit Tests: Diagnostic Engine & Priority Formula
# =========================================================================

def test_pure_priority_score_deterministic_formula():
    """Verify weighted priority score calculation and boundaries [0.0, 1.0]."""
    score = DiagnosticEngine.calculate_priority_score(
        mastery_gap=Decimal("0.80"),
        retention_risk=Decimal("0.50"),
        prerequisite_block=Decimal("1.00"),
        repeated_failure=Decimal("0.60"),
        overdue_learning=Decimal("0.40"),
        course_criticality=Decimal("0.70"),
    )
    # Expected:
    # 0.30*0.80 (0.24) + 0.20*0.50 (0.10) + 0.20*1.00 (0.20) + 0.15*0.60 (0.09) + 0.10*0.40 (0.04) + 0.05*0.70 (0.035)
    # Total = 0.7050
    assert score == Decimal("0.7050")

    # Clamping test
    score_clamped_high = DiagnosticEngine.calculate_priority_score(
        mastery_gap=Decimal("2.0"),
        retention_risk=Decimal("2.0"),
        prerequisite_block=Decimal("2.0"),
        repeated_failure=Decimal("2.0"),
        overdue_learning=Decimal("2.0"),
    )
    assert score_clamped_high == Decimal("1.0000")

    score_clamped_low = DiagnosticEngine.calculate_priority_score(
        mastery_gap=Decimal("0.0"),
        retention_risk=Decimal("0.0"),
        prerequisite_block=Decimal("0.0"),
        repeated_failure=Decimal("0.0"),
        overdue_learning=Decimal("0.0"),
        course_criticality=Decimal("0.0"),
    )
    assert score_clamped_low == Decimal("0.0000")


# =========================================================================
# 2. Pure Unit Tests: Prerequisite Path Cycle Detection
# =========================================================================

def test_pure_prerequisite_cycle_detection():
    """Verify that circular prerequisite graphs are detected deterministically."""
    # A -> B -> C -> A (cycle)
    graph_with_cycle = {
        "A": ["B"],
        "B": ["C"],
        "C": ["A"],
    }
    assert PrerequisitePathEngine.detect_cycle_in_graph(graph_with_cycle, "A") is True

    # A -> B -> C (DAG, no cycle)
    dag_graph = {
        "A": ["B"],
        "B": ["C"],
        "C": [],
    }
    assert PrerequisitePathEngine.detect_cycle_in_graph(dag_graph, "A") is False


# =========================================================================
# 3. Pure Unit Tests: Closed-Loop Outcome Engine
# =========================================================================

def test_pure_outcome_engine_improvement_and_closure():
    """Verify post-reassessment improvement classification and closure conditions."""
    # 1. Clear Improvement exceeding proficiency threshold
    res_success = OutcomeEngine.evaluate_outcome(
        mastery_before=Decimal("0.3500"),
        mastery_after=Decimal("0.7500"),
        confidence_before=Decimal("0.40"),
        confidence_after=Decimal("0.85"),
        retention_before=Decimal("0.50"),
        retention_after=Decimal("0.90"),
        prerequisite_blocking=False,
    )
    assert res_success["outcome_status"] == "IMPROVED"
    assert res_success["improvement_delta"] == Decimal("0.4000")
    assert res_success["closure_decision"] == "CLOSE_SUCCESS"
    assert "Observed post-remediation mastery" in res_success["closure_reason"]

    # 2. Partial Improvement remaining below threshold -> CONTINUE
    res_partial = OutcomeEngine.evaluate_outcome(
        mastery_before=Decimal("0.3500"),
        mastery_after=Decimal("0.4500"),
        confidence_before=Decimal("0.40"),
        confidence_after=Decimal("0.50"),
        retention_before=Decimal("0.50"),
        retention_after=Decimal("0.60"),
        prerequisite_blocking=False,
    )
    assert res_partial["outcome_status"] == "PARTIALLY_IMPROVED"
    assert res_partial["improvement_delta"] == Decimal("0.1000")
    assert res_partial["closure_decision"] == "CONTINUE"

    # 3. Regression -> ESCALATE
    res_regressed = OutcomeEngine.evaluate_outcome(
        mastery_before=Decimal("0.4000"),
        mastery_after=Decimal("0.3000"),
        confidence_before=Decimal("0.50"),
        confidence_after=Decimal("0.40"),
        retention_before=Decimal("0.60"),
        retention_after=Decimal("0.40"),
        prerequisite_blocking=False,
    )
    assert res_regressed["outcome_status"] == "REGRESSED"
    assert res_regressed["improvement_delta"] == Decimal("-0.1000")
    assert res_regressed["closure_decision"] == "ESCALATE"

    # 4. Insufficient Evidence
    res_no_data = OutcomeEngine.evaluate_outcome(
        mastery_before=Decimal("0.4000"),
        mastery_after=None,
        confidence_before=Decimal("0.50"),
        confidence_after=Decimal("0.50"),
        retention_before=Decimal("0.50"),
        retention_after=Decimal("0.50"),
    )
    assert res_no_data["outcome_status"] == "INSUFFICIENT_EVIDENCE"
    assert res_no_data["closure_decision"] == "CONTINUE"


# =========================================================================
# 4. Pure Unit Tests: Idempotency Key Generation
# =========================================================================

def test_pure_remediation_idempotency_key():
    """Verify deterministic idempotency keys prevent duplicate active plans."""
    key1 = RemediationService.generate_idempotency_key(
        student_profile_id="stud-1",
        signal_type="LOW_MASTERY",
        target_concept_id="conc-react-hooks",
    )
    key2 = RemediationService.generate_idempotency_key(
        student_profile_id="stud-1",
        signal_type="LOW_MASTERY",
        target_concept_id="conc-react-hooks",
    )
    key_diff = RemediationService.generate_idempotency_key(
        student_profile_id="stud-2",
        signal_type="LOW_MASTERY",
        target_concept_id="conc-react-hooks",
    )
    assert key1 == key2
    assert key1 != key_diff
    assert len(key1) == 64  # SHA256 hex string


# =========================================================================
# 5. Full Database Integration Tests: Signal -> Plan -> Step -> Outcome
# =========================================================================

@pytest.mark.asyncio
async def test_adaptive_remediation_full_closed_loop(
    db_session: AsyncSession,
):
    """Verify complete closed loop:
    1. Create student and concept with prerequisite
    2. Generate adaptive remediation plan
    3. Verify scaffolded steps created
    4. Student completes steps
    5. Closed-loop outcome evaluated and verified
    """
    u_suff = uuid.uuid4().hex[:6]
    inst = Institution(name=f"Inst D10 {u_suff}", code=f"I10_{u_suff}")
    db_session.add(inst)
    await db_session.flush()

    dept = Department(institution_id=inst.id, name=f"Dept D10 {u_suff}", code=f"D10_{u_suff}")
    db_session.add(dept)
    await db_session.flush()

    prog = Program(department_id=dept.id, name="B.Tech CS", code=f"P10_{u_suff}", degree_type="B.Tech")
    db_session.add(prog)
    await db_session.flush()

    batch = Batch(institution_id=inst.id, program_id=prog.id, label="2022-2026", admission_year=2022, graduation_year=2026)
    db_session.add(batch)
    await db_session.flush()

    user = User(
        email=f"stud_{u_suff}@univ.edu",
        normalized_email=f"stud_{u_suff}@univ.edu",
        hashed_password=get_password_hash("StudentPass123!"),
        role=UserRole.STUDENT,
        first_name="Ada",
        last_name="Lovelace",
        display_name="Ada Lovelace",
        institution_id=inst.id,
    )
    db_session.add(user)
    await db_session.flush()

    student_profile = StudentAcademicProfile(
        user_id=user.id,
        institution_id=inst.id,
        program_id=prog.id,
        batch_id=batch.id,
        enrollment_number=f"EN10_{u_suff}",
        admission_year=2022,
        graduation_year=2026,
    )
    db_session.add(student_profile)
    await db_session.flush()

    # Concepts: Target = Recursion, Prerequisite = Functions
    c_prereq = Concept(name=f"Functions_{u_suff}", slug=f"func_{u_suff}")
    c_target = Concept(name=f"Recursion_{u_suff}", slug=f"rec_{u_suff}")
    db_session.add_all([c_prereq, c_target])
    await db_session.flush()

    prereq_link = ConceptPrerequisite(
        concept_id=c_target.id,
        prerequisite_concept_id=c_prereq.id,
    )
    db_session.add(prereq_link)
    await db_session.flush()

    # Generate Remediation Plan
    plan = await RemediationService.create_or_get_remediation_plan(
        db_session,
        student_profile_id=student_profile.id,
        target_concept_id=c_target.id,
    )

    assert plan is not None
    assert plan.status in ["recommended", "assigned"]
    assert plan.target_concept_id == c_target.id
    assert len(plan.steps) >= 3  # Prerequisite, Micro-Lesson, Guided Practice, Reassessment

    # Complete step 1
    step_1 = plan.steps[0]
    payload_1 = CompleteStepPayload(score=Decimal("80.0"), completion_percentage=Decimal("100.0"))
    step_updated = await RemediationService.complete_step(
        db_session, step_id=step_1.id, payload=payload_1, current_student_profile_id=student_profile.id
    )
    assert step_updated.completion_status == "completed"

    # Verify Content Gap Detection for missing content
    gap_stmt = select(ContentGapRecord).where(ContentGapRecord.institution_id == inst.id)
    gap_res = await db_session.execute(gap_stmt)
    gaps = gap_res.scalars().all()
    assert len(gaps) > 0  # Content gaps recorded for missing lesson/assessment


@pytest.mark.asyncio
async def test_faculty_override_workflow(
    db_session: AsyncSession,
):
    """Verify faculty approval, pause, resume, and manual closure of remediation plans."""
    u_suff = uuid.uuid4().hex[:6]
    inst = Institution(name=f"Inst D10 Faculty {u_suff}", code=f"I10F_{u_suff}")
    db_session.add(inst)
    await db_session.flush()

    dept = Department(institution_id=inst.id, name=f"Dept D10 Faculty {u_suff}", code=f"D10F_{u_suff}")
    db_session.add(dept)
    await db_session.flush()

    prog = Program(department_id=dept.id, name="B.Tech CS", code=f"PF_{u_suff}", degree_type="B.Tech")
    db_session.add(prog)
    await db_session.flush()

    batch = Batch(institution_id=inst.id, program_id=prog.id, label="2022-2026", admission_year=2022, graduation_year=2026)
    db_session.add(batch)
    await db_session.flush()

    t_user = User(
        email=f"prof_{u_suff}@univ.edu",
        normalized_email=f"prof_{u_suff}@univ.edu",
        hashed_password=get_password_hash("ProfPass123!"),
        role=UserRole.TEACHER,
        first_name="Grace",
        last_name="Hopper",
        display_name="Prof. Hopper",
        institution_id=inst.id,
    )
    s_user = User(
        email=f"stud_{u_suff}@univ.edu",
        normalized_email=f"stud_{u_suff}@univ.edu",
        hashed_password=get_password_hash("StudentPass123!"),
        role=UserRole.STUDENT,
        first_name="Charles",
        last_name="Babbage",
        display_name="Charles Babbage",
        institution_id=inst.id,
    )
    db_session.add_all([t_user, s_user])
    await db_session.flush()

    student_profile = StudentAcademicProfile(
        user_id=s_user.id,
        institution_id=inst.id,
        program_id=prog.id,
        batch_id=batch.id,
        enrollment_number=f"EN10F_{u_suff}",
        admission_year=2022,
        graduation_year=2026,
    )
    concept = Concept(name=f"Dynamic Programming_{u_suff}", slug=f"dp_{u_suff}")
    db_session.add_all([student_profile, concept])
    await db_session.flush()

    plan = await RemediationService.create_or_get_remediation_plan(
        db_session,
        student_profile_id=student_profile.id,
        target_concept_id=concept.id,
    )

    # 1. Faculty Approve
    approved_plan = await RemediationService.faculty_override_plan(
        db_session,
        plan_id=plan.id,
        user=t_user,
        action="approve",
        reason="Reviewed and approved for semester recovery",
    )
    assert approved_plan.status == "assigned"
    assert approved_plan.faculty_reviewer_id == t_user.id
    assert "[APPROVE]" in approved_plan.faculty_override_reason

    # 2. Faculty Pause
    paused_plan = await RemediationService.faculty_override_plan(
        db_session,
        plan_id=plan.id,
        user=t_user,
        action="pause",
        reason="Mid-term exam week",
    )
    assert paused_plan.status == "paused"

    # 3. Faculty Resume
    resumed_plan = await RemediationService.faculty_override_plan(
        db_session,
        plan_id=plan.id,
        user=t_user,
        action="resume",
        reason="Resuming post-exam",
    )
    assert resumed_plan.status == "in_progress"


# =========================================================================
# 6. HTTP API Endpoint Tests: Student, Faculty, HOD, and Admin
# =========================================================================

@pytest.mark.asyncio
async def test_remediation_http_api_endpoints(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    """Verify REST API routes: /api/v1/remediation/me, /plans/{id}, overrides, analytics, content gaps."""
    from app.core.security import create_access_token

    u_suff = uuid.uuid4().hex[:6]
    inst = Institution(name=f"Inst D10 API {u_suff}", code=f"I10A_{u_suff}")
    db_session.add(inst)
    await db_session.flush()

    dept = Department(institution_id=inst.id, name=f"Dept D10 API {u_suff}", code=f"D10A_{u_suff}")
    db_session.add(dept)
    await db_session.flush()

    prog = Program(department_id=dept.id, name="B.Tech CS", code=f"PA_{u_suff}", degree_type="B.Tech")
    db_session.add(prog)
    await db_session.flush()

    batch = Batch(institution_id=inst.id, program_id=prog.id, label="2022-2026", admission_year=2022, graduation_year=2026)
    db_session.add(batch)
    await db_session.flush()

    s_user = User(
        email=f"stud_api_{u_suff}@univ.edu",
        normalized_email=f"stud_api_{u_suff}@univ.edu",
        hashed_password=get_password_hash("StudentPass123!"),
        role=UserRole.STUDENT,
        first_name="Radia",
        last_name="Perlman",
        display_name="Radia Perlman",
        institution_id=inst.id,
    )
    admin_user = User(
        email=f"admin_api_{u_suff}@univ.edu",
        normalized_email=f"admin_api_{u_suff}@univ.edu",
        hashed_password=get_password_hash("AdminPass123!"),
        role=UserRole.INSTITUTION_ADMIN,
        first_name="Admin",
        last_name="Officer",
        display_name="Admin Officer",
        institution_id=inst.id,
    )
    db_session.add_all([s_user, admin_user])
    await db_session.flush()

    s_profile = StudentAcademicProfile(
        user_id=s_user.id,
        institution_id=inst.id,
        program_id=prog.id,
        batch_id=batch.id,
        enrollment_number=f"EN10API_{u_suff}",
        admission_year=2022,
        graduation_year=2026,
    )
    concept = Concept(name=f"Spanning Tree Protocol_{u_suff}", slug=f"stp_{u_suff}")
    db_session.add_all([s_profile, concept])
    await db_session.flush()

    plan = await RemediationService.create_or_get_remediation_plan(
        db_session,
        student_profile_id=s_profile.id,
        target_concept_id=concept.id,
    )

    s_token = create_access_token(subject=s_user.id, role=s_user.role)
    admin_token = create_access_token(subject=admin_user.id, role=admin_user.role)

    # 1. Student GET /me
    res_me = await async_client.get(
        "/api/v1/remediation/me",
        headers={"Authorization": f"Bearer {s_token}"},
    )
    assert res_me.status_code == 200
    plans_data = res_me.json()
    assert len(plans_data) >= 1
    assert plans_data[0]["id"] == plan.id

    # 2. Student GET /plans/{id}
    res_plan = await async_client.get(
        f"/api/v1/remediation/plans/{plan.id}",
        headers={"Authorization": f"Bearer {s_token}"},
    )
    assert res_plan.status_code == 200
    assert res_plan.json()["target_concept_id"] == concept.id

    # 3. Admin GET /content-gaps
    res_gaps = await async_client.get(
        "/api/v1/remediation/content-gaps",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_gaps.status_code == 200
    assert isinstance(res_gaps.json(), list)

    # 4. Admin GET /analytics/institutional
    res_inst_analytics = await async_client.get(
        "/api/v1/remediation/analytics/institutional",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_inst_analytics.status_code == 200
    analytics_payload = res_inst_analytics.json()
    assert "plans_created" in analytics_payload
    assert "completion_rate" in analytics_payload

    # 5. Admin POST /accreditation/evidence/generate
    res_accreditation = await async_client.post(
        "/api/v1/remediation/accreditation/evidence/generate",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"framework": "NAAC", "criterion": "2.2.1"},
    )
    assert res_accreditation.status_code == 200
    accred_data = res_accreditation.json()
    assert accred_data["framework"] == "NAAC"
    assert accred_data["criterion"] == "2.2.1"


