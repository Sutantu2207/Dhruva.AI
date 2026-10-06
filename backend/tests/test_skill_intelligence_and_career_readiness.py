"""Tests for Domain 7: Skill Intelligence, Career Trajectories & Placement Readiness Engine."""

import uuid
from decimal import Decimal
from datetime import datetime, timezone, date
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import create_access_token, UserRole
from app.domains.identity.models import User
from app.domains.academic.models import (
    Institution,
    Department,
    Program,
    Batch,
    StudentAcademicProfile,
)
from app.domains.catalog.models import (
    SkillCatalog,
    CareerCatalog,
    CareerSkillMapping,
)
from app.domains.profiles.models import (
    StudentSkill,
    StudentCareerGoal,
    StudentProject,
    StudentProjectSkill,
)
from app.domains.assessment.models import SkillEvidence, QuestionVersion, Question, QuestionBank
from app.domains.content.models import Concept, ConceptSkill, Lesson, CourseContent
from app.domains.mastery.models import StudentConceptKnowledgeState
from app.domains.career_intelligence.config import DEFAULT_CAREER_CONFIG
from app.domains.career_intelligence.skill_engine import (
    SkillIntelligenceEngine,
    SkillEvidenceInput,
)
from app.domains.career_intelligence.readiness_engine import (
    CareerReadinessEngine,
    CareerSkillReq,
)
from app.domains.career_intelligence.trajectory_engine import (
    CareerTrajectoryEngine,
)
from app.domains.career_intelligence.placement_engine import (
    PlacementReadinessEngine,
    PlacementEvaluationInput,
)
from app.domains.career_intelligence.service import career_intelligence_service


# =========================================================================
# 1. Pure Deterministic Skill Intelligence Tests
# =========================================================================

def test_pure_skill_intelligence_engine_and_weights():
    engine = SkillIntelligenceEngine(DEFAULT_CAREER_CONFIG)

    # A. Insufficient evidence
    res_empty = engine.evaluate_skill(
        skill_id="s1",
        evidence_items=[],
        self_reported_proficiency=None,
    )
    assert res_empty.observed_proficiency == Decimal("0.0000")
    assert res_empty.verified_proficiency == Decimal("0.0000")
    assert res_empty.confidence == Decimal("0.0000")
    assert res_empty.verification_status == "unverified"
    assert res_empty.proficiency_tier == "exposure"

    # B. Self-report only
    res_self = engine.evaluate_skill(
        skill_id="s1",
        evidence_items=[],
        self_reported_proficiency=Decimal("0.7000"),
    )
    assert res_self.observed_proficiency == Decimal("0.7000")
    assert res_self.verified_proficiency == Decimal("0.0000")
    assert res_self.verification_status == "unverified"

    # C. Assessment verified evidence
    items = [
        SkillEvidenceInput(source_type="assessment", source_id="a1", score=Decimal("0.8500"), is_verified=True),
        SkillEvidenceInput(source_type="assessment", source_id="a2", score=Decimal("0.8000"), is_verified=True),
        SkillEvidenceInput(source_type="coding_assessment", source_id="a3", score=Decimal("0.9000"), is_verified=True),
    ]
    res_asst = engine.evaluate_skill(
        skill_id="s1",
        evidence_items=items,
        self_reported_proficiency=Decimal("0.7000"),
        concept_mastery_score=Decimal("0.8800"),
    )
    assert res_asst.verified_proficiency > Decimal("0.8000")
    assert res_asst.confidence > Decimal("0.7000")
    assert res_asst.verification_status == "certified"
    assert res_asst.proficiency_tier == "advanced"

    # D. Invariant bounds
    assert Decimal("0.0000") <= res_asst.observed_proficiency <= Decimal("1.0000")
    assert Decimal("0.0000") <= res_asst.verified_proficiency <= Decimal("1.0000")
    assert Decimal("0.0000") <= res_asst.confidence <= Decimal("1.0000")


# =========================================================================
# 2. Pure Career Readiness & Gaps Tests
# =========================================================================

def test_pure_career_readiness_engine_and_gaps():
    engine = CareerReadinessEngine(DEFAULT_CAREER_CONFIG)

    reqs = [
        CareerSkillReq(skill_id="s1", skill_name="JavaScript", importance="critical", weight=Decimal("1.5"), min_proficiency=Decimal("0.7000")),
        CareerSkillReq(skill_id="s2", skill_name="React", importance="required", weight=Decimal("1.0"), min_proficiency=Decimal("0.6000")),
        CareerSkillReq(skill_id="s3", skill_name="TypeScript", importance="preferred", weight=Decimal("0.8"), min_proficiency=Decimal("0.5000")),
    ]

    # Full attainment
    skills_full = {
        "s1": Decimal("0.9000"),
        "s2": Decimal("0.8000"),
        "s3": Decimal("0.7500"),
    }
    res_full = engine.calculate_readiness("c1", "Full Stack Developer", reqs, skills_full)
    assert res_full.readiness_score == Decimal("1.0000")
    assert len(res_full.critical_gaps) == 0
    assert len(res_full.strengths) == 3

    # Partial attainment with critical gap
    skills_partial = {
        "s1": Decimal("0.2000"),  # Below critical min_proficiency 0.70
        "s2": Decimal("0.6500"),  # Meets required min_proficiency 0.60
        "s3": Decimal("0.1000"),  # Gap on preferred
    }
    res_partial = engine.calculate_readiness("c1", "Full Stack Developer", reqs, skills_partial)
    assert res_partial.readiness_score < Decimal("0.7000")
    assert len(res_partial.critical_gaps) == 1
    assert res_partial.critical_gaps[0].skill_id == "s1"
    assert res_partial.critical_gaps[0].severity == "critical"
    assert res_partial.explanation["critical_skills_below_threshold"] == 1


# =========================================================================
# 3. Pure Career Trajectory & Honest Content Availability
# =========================================================================

def test_pure_career_trajectory_engine_and_blocking():
    engine = CareerTrajectoryEngine("v1")

    from app.domains.career_intelligence.readiness_engine import SkillGapItem

    gaps = [
        SkillGapItem(
            skill_id="s_pref",
            skill_name="Docker",
            importance="preferred",
            current_proficiency=Decimal("0.1000"),
            required_proficiency=Decimal("0.5000"),
            gap_size=Decimal("0.4000"),
            severity="medium",
            reason="Preferred competency gap",
        ),
        SkillGapItem(
            skill_id="s_crit",
            skill_name="Data Structures",
            importance="critical",
            current_proficiency=Decimal("0.2000"),
            required_proficiency=Decimal("0.7500"),
            gap_size=Decimal("0.5500"),
            severity="critical",
            reason="Critical dependency below threshold",
        ),
    ]

    # Content mapping: s_crit has blocked concept, s_pref has no content
    concept_map = {"s_crit": [{"id": "c_trees", "name": "Trees & Graphs"}]}
    readiness_map = {"c_trees": Decimal("0.3500")}  # Weak prerequisite (< 0.50)

    res = engine.build_trajectory(
        career_id="car1",
        career_title="Software Engineer",
        gaps=gaps,
        skill_to_concept_map=concept_map,
        skill_to_lesson_map={},
        concept_readiness_map=readiness_map,
    )

    # Step 1 should be critical gap first
    assert res.steps[0].skill_id == "s_crit"
    assert res.steps[0].status == "blocked"

    # Step 2 should be s_pref with explicit not_available status (NO fake hallucination)
    assert res.steps[1].skill_id == "s_pref"
    assert res.steps[1].status == "not_available"
    assert "No mapped learning content available yet" in res.steps[1].title


# =========================================================================
# 4. Pure Placement Readiness Honesty Tests
# =========================================================================

def test_pure_placement_readiness_engine_honesty():
    engine = PlacementReadinessEngine("v1")

    # Unassessed profile
    input_unassessed = PlacementEvaluationInput(
        career_readiness_score=None,
        average_assessment_score=None,
        verified_projects_count=0,
    )
    res_unassessed = engine.evaluate_placement_readiness(input_unassessed)
    assert res_unassessed.overall_status == "not_yet_assessed"

    # Incomplete profile: technical + assessment assessed, but missing projects -> needs_portfolio
    input_incomplete = PlacementEvaluationInput(
        career_readiness_score=Decimal("0.7500"),
        average_assessment_score=Decimal("0.7000"),
        verified_projects_count=0,
        communication_score=None,
        resume_score=None,
        interview_score=None,
    )
    res_inc = engine.evaluate_placement_readiness(input_incomplete)
    assert res_inc.overall_status == "needs_portfolio"
    assert res_inc.component_statuses["interview"] == "not_assessed"
    assert res_inc.component_statuses["resume"] == "not_assessed"
    assert res_inc.component_statuses["communication"] == "not_assessed"

    # Profile with technical + projects verified
    input_ready = PlacementEvaluationInput(
        career_readiness_score=Decimal("0.8500"),
        average_assessment_score=Decimal("0.8000"),
        verified_projects_count=3,
        project_score_average=Decimal("0.8500"),
        communication_score=Decimal("0.7500"),
        resume_score=Decimal("0.8000"),
        interview_score=Decimal("0.7800"),
        career_goal_match=True,
    )
    res_ready = engine.evaluate_placement_readiness(input_ready)
    assert res_ready.overall_status == "placement_ready"
    assert res_ready.technical_readiness == Decimal("0.8500")


# =========================================================================
# 5. Integration: Multi-Source Evidence Ingestion & Career Trajectory
# =========================================================================

@pytest.mark.asyncio
async def test_career_intelligence_integration_lifecycle(db_session: AsyncSession):
    # Setup Institution hierarchy
    inst = Institution(name=f"IIT Bombay {uuid.uuid4().hex[:6]}", code=f"IITB_{uuid.uuid4().hex[:4]}")
    db_session.add(inst)
    await db_session.flush()

    dept = Department(institution_id=inst.id, name="Computer Science", code=f"CS_{uuid.uuid4().hex[:4]}")
    db_session.add(dept)
    await db_session.flush()

    prog = Program(department_id=dept.id, name="B.Tech CS", code=f"P_{uuid.uuid4().hex[:4]}", degree_type="B")
    db_session.add(prog)
    await db_session.flush()

    batch = Batch(institution_id=inst.id, program_id=prog.id, admission_year=2026, graduation_year=2030, label="2026-2030")
    db_session.add(batch)
    await db_session.flush()

    user = User(
        email=f"student_{uuid.uuid4().hex[:6]}@dhruva.edu",
        normalized_email=f"student_{uuid.uuid4().hex[:6]}@dhruva.edu",
        first_name="Rohan",
        last_name="Sharma",
        display_name="Rohan Sharma",
        role="student",
        institution_id=inst.id,
        hashed_password="hash",
    )
    db_session.add(user)
    await db_session.flush()

    prof = StudentAcademicProfile(
        user_id=user.id,
        institution_id=inst.id,
        program_id=prog.id,
        batch_id=batch.id,
        enrollment_number=f"ENR_{uuid.uuid4().hex[:6]}",
        admission_year=2026,
        graduation_year=2030,
    )
    db_session.add(prof)
    await db_session.flush()

    # Skills & Career in catalog
    skill_js = SkillCatalog(code=f"SKL-JS-{uuid.uuid4().hex[:4]}", name="JavaScript", slug=f"js-{uuid.uuid4().hex[:4]}", status="active")
    skill_py = SkillCatalog(code=f"SKL-PY-{uuid.uuid4().hex[:4]}", name="Python", slug=f"py-{uuid.uuid4().hex[:4]}", status="active")
    skill_db = SkillCatalog(code=f"SKL-DB-{uuid.uuid4().hex[:4]}", name="Databases", slug=f"db-{uuid.uuid4().hex[:4]}", status="active")
    db_session.add_all([skill_js, skill_py, skill_db])
    await db_session.flush()

    career = CareerCatalog(code=f"CAR-DEV-{uuid.uuid4().hex[:4]}", title="Full Stack Developer", slug=f"fsd-{uuid.uuid4().hex[:4]}", status="active")
    db_session.add(career)
    await db_session.flush()

    # Map career requirements
    m1 = CareerSkillMapping(career_id=career.id, skill_id=skill_js.id, importance="required", weight=1.0)
    m2 = CareerSkillMapping(career_id=career.id, skill_id=skill_db.id, importance="critical", weight=1.5)
    db_session.add_all([m1, m2])
    await db_session.flush()

    # Set student career goal
    c_goal = StudentCareerGoal(student_profile_id=prof.id, career_catalog_id=career.id, priority=1)
    db_session.add(c_goal)
    await db_session.flush()

    # Add verified project demonstrating JavaScript
    proj = StudentProject(
        student_profile_id=prof.id,
        title="E-Commerce API",
        status="completed",
        is_verified=True,
    )
    db_session.add(proj)
    await db_session.flush()

    p_skill = StudentProjectSkill(project_id=proj.id, skill_catalog_id=skill_js.id)
    db_session.add(p_skill)
    await db_session.flush()

    # Add question version for assessment evidence
    qbank = QuestionBank(institution_id=inst.id, title="Core CS Bank")
    db_session.add(qbank)
    await db_session.flush()

    q = Question(bank_id=qbank.id, question_type="single_choice", title="JS Closures Question")
    db_session.add(q)
    await db_session.flush()

    qv = QuestionVersion(question_id=q.id, version_number=1, prompt="JS Closures Prompt", difficulty="medium")
    db_session.add(qv)
    await db_session.flush()

    # Ingest Domain 5 SkillEvidence on JavaScript
    ev = SkillEvidence(
        student_profile_id=prof.id,
        skill_id=skill_js.id,
        question_version_id=qv.id,
        score=Decimal("0.8500"),
        weight=Decimal("1.00"),
        evidence_type="assessment",
    )
    db_session.add(ev)
    await db_session.commit()

    # Execute Service Evaluations
    evaluated_skills = await career_intelligence_service.evaluate_all_student_skills(db_session, prof.id)
    assert skill_js.id in evaluated_skills
    js_state = evaluated_skills[skill_js.id]
    assert js_state.verified_proficiency > Decimal("0.8000")
    assert js_state.verification_status in ["verified", "certified"]

    # Evaluate Career Readiness
    c_state, calc_res = await career_intelligence_service.evaluate_career_readiness(db_session, prof.id, career.id)
    assert c_state.readiness_score > Decimal("0.3000")
    assert len(calc_res.critical_gaps) == 1
    assert calc_res.critical_gaps[0].skill_id == skill_db.id  # Databases has no evidence yet

    # Generate Trajectory
    traj = await career_intelligence_service.generate_career_trajectory(db_session, prof.id, career.id)
    assert traj.total_steps >= 1
    assert traj.steps[0].skill_id == skill_db.id

    # Evaluate Placement Readiness
    p_state = await career_intelligence_service.evaluate_placement_readiness(db_session, prof.id)
    assert p_state.technical_readiness is not None
    assert p_state.project_evidence_score is not None


# =========================================================================
# 6. REST API Endpoints & RBAC Scoping Tests
# =========================================================================

@pytest.mark.asyncio
async def test_career_api_endpoints_and_security(async_client: AsyncClient, db_session: AsyncSession):
    inst1 = Institution(name=f"Inst1 {uuid.uuid4().hex[:4]}", code=f"I1_{uuid.uuid4().hex[:4]}")
    inst2 = Institution(name=f"Inst2 {uuid.uuid4().hex[:4]}", code=f"I2_{uuid.uuid4().hex[:4]}")
    db_session.add_all([inst1, inst2])
    await db_session.flush()

    dept1 = Department(institution_id=inst1.id, name="CS", code=f"CS1_{uuid.uuid4().hex[:4]}")
    dept2 = Department(institution_id=inst2.id, name="CS", code=f"CS2_{uuid.uuid4().hex[:4]}")
    db_session.add_all([dept1, dept2])
    await db_session.flush()

    prog1 = Program(department_id=dept1.id, name="B.Tech", code=f"P1_{uuid.uuid4().hex[:4]}", degree_type="B")
    prog2 = Program(department_id=dept2.id, name="B.Tech", code=f"P2_{uuid.uuid4().hex[:4]}", degree_type="B")
    db_session.add_all([prog1, prog2])
    await db_session.flush()

    batch1 = Batch(institution_id=inst1.id, program_id=prog1.id, admission_year=2026, graduation_year=2030, label="B1")
    batch2 = Batch(institution_id=inst2.id, program_id=prog2.id, admission_year=2026, graduation_year=2030, label="B2")
    db_session.add_all([batch1, batch2])
    await db_session.flush()

    stud1 = User(email=f"s1_{uuid.uuid4().hex[:6]}@i1.edu", normalized_email=f"s1_{uuid.uuid4().hex[:6]}@i1.edu", first_name="S1", last_name="U", display_name="S1 U", role="student", institution_id=inst1.id, hashed_password="h")
    stud2 = User(email=f"s2_{uuid.uuid4().hex[:6]}@i2.edu", normalized_email=f"s2_{uuid.uuid4().hex[:6]}@i2.edu", first_name="S2", last_name="U", display_name="S2 U", role="student", institution_id=inst2.id, hashed_password="h")
    teacher1 = User(email=f"t1_{uuid.uuid4().hex[:6]}@i1.edu", normalized_email=f"t1_{uuid.uuid4().hex[:6]}@i1.edu", first_name="T1", last_name="U", display_name="T1 U", role="teacher", institution_id=inst1.id, hashed_password="h")
    db_session.add_all([stud1, stud2, teacher1])
    await db_session.flush()

    prof1 = StudentAcademicProfile(user_id=stud1.id, institution_id=inst1.id, program_id=prog1.id, batch_id=batch1.id, enrollment_number=f"EN1_{uuid.uuid4().hex[:6]}", admission_year=2026, graduation_year=2030)
    prof2 = StudentAcademicProfile(user_id=stud2.id, institution_id=inst2.id, program_id=prog2.id, batch_id=batch2.id, enrollment_number=f"EN2_{uuid.uuid4().hex[:6]}", admission_year=2026, graduation_year=2030)
    db_session.add_all([prof1, prof2])
    await db_session.flush()

    career = CareerCatalog(code=f"CAR-AI-{uuid.uuid4().hex[:4]}", title="AI Engineer", slug=f"ai-{uuid.uuid4().hex[:4]}", status="active")
    skill = SkillCatalog(code=f"SKL-ML-{uuid.uuid4().hex[:4]}", name="Machine Learning", slug=f"ml-{uuid.uuid4().hex[:4]}", status="active")
    db_session.add_all([career, skill])
    await db_session.flush()

    c_map = CareerSkillMapping(career_id=career.id, skill_id=skill.id, importance="required", weight=1.0)
    db_session.add(c_map)
    await db_session.commit()

    token_stud1 = create_access_token(subject=stud1.id, role=UserRole.STUDENT, institution_id=inst1.id)
    token_stud2 = create_access_token(subject=stud2.id, role=UserRole.STUDENT, institution_id=inst2.id)
    token_teacher1 = create_access_token(subject=teacher1.id, role=UserRole.TEACHER, institution_id=inst1.id)

    client = async_client

    # 1. Student 1 Career Intelligence
    resp = await client.get("/api/v1/career/intelligence", headers={"Authorization": f"Bearer {token_stud1}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "target_career" in data
    assert "readiness" in data
    assert "trajectory" in data

    # 2. Student 1 Skills List
    resp_skills = await client.get("/api/v1/skills", headers={"Authorization": f"Bearer {token_stud1}"})
    assert resp_skills.status_code == 200

    # 3. Teacher 1 checks student in own institution -> 200
    resp_teacher_ok = await client.get(
        f"/api/v1/students/{prof1.id}/career/intelligence",
        headers={"Authorization": f"Bearer {token_teacher1}"},
    )
    assert resp_teacher_ok.status_code == 200

    # 4. Teacher 1 checks student in different institution -> 403 Forbidden
    resp_teacher_cross = await client.get(
        f"/api/v1/students/{prof2.id}/career/intelligence",
        headers={"Authorization": f"Bearer {token_teacher1}"},
    )
    assert resp_teacher_cross.status_code == 403
