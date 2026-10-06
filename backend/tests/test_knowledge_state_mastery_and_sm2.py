"""Comprehensive Test Suite for Domain 6: Knowledge State, Concept Mastery & Spaced Repetition (SM-2)."""

import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

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
    StudentEnrollment,
)
from app.domains.content.models import Concept, ConceptPrerequisite
from app.domains.assessment.models import (
    QuestionBank,
    Question,
    QuestionVersion,
    Assessment,
    AssessmentVersion,
    AssessmentAttempt,
    ConceptEvidence,
)
from app.domains.mastery.clock import FrozenClock
from app.domains.mastery.config import KnowledgeStateConfig, DEFAULT_KNOWLEDGE_CONFIG
from app.domains.mastery.mastery_engine import (
    ConceptMasteryEngine,
    EvidenceItemDTO,
    MasteryEvaluationOutput,
)
from app.domains.mastery.retention_engine import RetentionEngine
from app.domains.mastery.sm2_scheduler import SM2Scheduler
from app.domains.mastery.prerequisite_engine import PrerequisiteReadinessEngine
from app.domains.mastery.priority_engine import (
    LearningPriorityEngine,
    ConceptStateContext,
    PriorityEvaluationResult,
)
from app.domains.mastery.service import KnowledgeStateService
from app.domains.mastery.models import (
    StudentConceptKnowledgeState,
    KnowledgeStateHistory,
    ConceptEvidenceProcessing,
    ConceptReviewState,
    ConceptReviewHistory,
)


# =========================================================================
# 1. Pure Deterministic Unit & Property Invariant Tests
# =========================================================================

def test_pure_concept_mastery_engine_and_invariants():
    """Verifies pure ConceptMasteryEngine calculations, weights, and property invariants."""
    frozen_clock = FrozenClock(datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc))
    now = frozen_clock.now()

    # 1. Empty evidence -> Unknown state
    empty_res = ConceptMasteryEngine.evaluate(
        concept_id="c-binary-search",
        evidence_items=[],
        now=now,
    )
    assert empty_res.mastery is None
    assert empty_res.state == "unknown"
    assert empty_res.confidence == Decimal("0.0000")
    assert empty_res.trend == "insufficient_data"

    # 2. Single evidence item -> Introduced state, low confidence
    single_ev = [
        EvidenceItemDTO(
            id="ev-1",
            concept_id="c-binary-search",
            score=Decimal("0.9000"),
            max_score=Decimal("1.0000"),
            evidence_type="assessment",
            difficulty="medium",
            timestamp=now,
        )
    ]
    single_res = ConceptMasteryEngine.evaluate(
        concept_id="c-binary-search",
        evidence_items=single_ev,
        now=now,
    )
    assert single_res.state == "introduced"
    assert single_res.evidence_count == 1
    assert single_res.confidence <= Decimal("0.3000")

    # 3. Multiple consistent high observations -> Mastered state
    high_ev = [
        EvidenceItemDTO(
            id="ev-1",
            concept_id="c-binary-search",
            score=Decimal("0.9500"),
            max_score=Decimal("1.0000"),
            evidence_type="assessment",
            difficulty="medium",
            timestamp=now - timedelta(days=5),
        ),
        EvidenceItemDTO(
            id="ev-2",
            concept_id="c-binary-search",
            score=Decimal("0.9000"),
            max_score=Decimal("1.0000"),
            evidence_type="assessment",
            difficulty="hard",
            timestamp=now - timedelta(days=2),
        ),
        EvidenceItemDTO(
            id="ev-3",
            concept_id="c-binary-search",
            score=Decimal("1.0000"),
            max_score=Decimal("1.0000"),
            evidence_type="practice",
            difficulty="medium",
            timestamp=now,
        ),
    ]
    high_res = ConceptMasteryEngine.evaluate(
        concept_id="c-binary-search",
        evidence_items=high_ev,
        now=now,
    )
    assert high_res.mastery is not None
    assert high_res.mastery >= Decimal("0.8500")
    assert high_res.state == "mastered"
    assert high_res.confidence >= Decimal("0.5000")
    assert high_res.trend in ("stable", "improving", "strongly_improving")

    # Property Invariants
    assert Decimal("0.0000") <= high_res.mastery <= Decimal("1.0000")
    assert Decimal("0.0000") <= high_res.confidence <= Decimal("1.0000")


def test_pure_retention_engine_and_ebbinghaus_decay():
    """Verifies that retention decays with elapsed time while mastery remains stable."""
    frozen_clock = FrozenClock(datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc))
    now = frozen_clock.now()

    # Immediate retention (0 days elapsed)
    r_day0 = RetentionEngine.estimate_retention(
        last_event_at=now,
        interval_days=1,
        ease_factor=Decimal("2.5000"),
        now=now,
    )
    assert r_day0 == Decimal("1.0000")

    # Retention after 1 day
    r_day1 = RetentionEngine.estimate_retention(
        last_event_at=now,
        interval_days=1,
        ease_factor=Decimal("2.5000"),
        now=now + timedelta(days=1),
    )
    assert r_day1 < r_day0
    assert r_day1 > Decimal("0.3000")

    # Retention after 7 days without review
    r_day7 = RetentionEngine.estimate_retention(
        last_event_at=now,
        interval_days=1,
        ease_factor=Decimal("2.5000"),
        now=now + timedelta(days=7),
    )
    assert r_day7 < r_day1

    # Invariants
    assert Decimal("0.0000") <= r_day7 <= Decimal("1.0000")


def test_pure_sm2_scheduler_quality_and_transitions():
    """Verifies SM-2 algorithm schedule transitions across qualities 0 through 5."""
    frozen_clock = FrozenClock(datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc))
    now = frozen_clock.now()

    # 1. Initialization
    init_res = SM2Scheduler.initialize_schedule(now=now)
    assert init_res.repetition == 0
    assert init_res.interval_days == 1
    assert init_res.ease_factor == Decimal("2.5000")
    assert init_res.next_review_at == now + timedelta(days=1)

    # 2. Perfect recall (Quality 5) on first review
    q5_res = SM2Scheduler.calculate_next_schedule(
        quality=5,
        previous_repetition=0,
        previous_interval_days=1,
        previous_ease_factor=Decimal("2.5000"),
        now=now,
    )
    assert q5_res.repetition == 1
    assert q5_res.interval_days == 1
    assert q5_res.ease_factor >= Decimal("2.5000")  # EF increases

    # 3. Second successful review (Quality 4) -> interval jumps to 6 days
    q4_res = SM2Scheduler.calculate_next_schedule(
        quality=4,
        previous_repetition=1,
        previous_interval_days=1,
        previous_ease_factor=q5_res.ease_factor,
        now=now,
    )
    assert q4_res.repetition == 2
    assert q4_res.interval_days == 6

    # 4. Third successful review (Quality 4) -> interval = round(6 * EF)
    q4_res_3 = SM2Scheduler.calculate_next_schedule(
        quality=4,
        previous_repetition=2,
        previous_interval_days=6,
        previous_ease_factor=q4_res.ease_factor,
        now=now,
    )
    assert q4_res_3.repetition == 3
    assert q4_res_3.interval_days >= 14

    # 5. Failed recall (Quality 1 or 2) -> resets repetition streak to 0, interval to 1
    failed_res = SM2Scheduler.calculate_next_schedule(
        quality=1,
        previous_repetition=3,
        previous_interval_days=14,
        previous_ease_factor=q4_res_3.ease_factor,
        now=now,
    )
    assert failed_res.repetition == 0
    assert failed_res.interval_days == 1
    assert failed_res.ease_factor >= Decimal("1.3000")  # Ease floor protected


def test_pure_prerequisite_readiness_and_cycle_defense():
    """Verifies prerequisite graph readiness calculations and cyclic dependency defense."""
    graph = {
        "binary_search": ["arrays", "searching"],
        "trees": ["recursion"],
        "cyclic_a": ["cyclic_b"],
        "cyclic_b": ["cyclic_a"],
    }

    # High prerequisite mastery
    masteries_high = {
        "arrays": Decimal("0.9000"),
        "searching": Decimal("0.8500"),
    }
    score, health = PrerequisiteReadinessEngine.evaluate_readiness("binary_search", graph, masteries_high)
    assert score is not None and score >= Decimal("0.8500")
    assert health == "healthy"

    # Weak prerequisite mastery
    masteries_weak = {
        "recursion": Decimal("0.3000"),
    }
    score_w, health_w = PrerequisiteReadinessEngine.evaluate_readiness("trees", graph, masteries_weak)
    assert score_w is not None and score_w < Decimal("0.4000")
    assert health_w == "weak"

    # Cyclic graph safety (must terminate without recursion overflow)
    score_c, health_c = PrerequisiteReadinessEngine.evaluate_readiness(
        "cyclic_a", graph, {"cyclic_b": Decimal("0.7000")}
    )
    assert health_c in ("healthy", "partial")


def test_pure_learning_priority_and_daily_mission():
    """Verifies deterministic learning priority scoring and daily mission generation."""
    c1 = ConceptStateContext(
        concept_id="c-recursion",
        concept_name="Recursion",
        mastery=Decimal("0.4000"),
        retention_estimate=Decimal("0.4500"),
        review_status="overdue",
        prerequisite_health="healthy",
    )
    c2 = ConceptStateContext(
        concept_id="c-arrays",
        concept_name="Arrays",
        mastery=Decimal("0.9500"),
        retention_estimate=Decimal("0.9000"),
        review_status="upcoming",
        prerequisite_health="healthy",
    )

    eval_c1 = LearningPriorityEngine.evaluate_concept_priority(c1)
    eval_c2 = LearningPriorityEngine.evaluate_concept_priority(c2)

    # Urgent, low-mastery, overdue concept must have significantly higher priority
    assert eval_c1.priority_score > eval_c2.priority_score
    assert "REVIEW_OVERDUE" in eval_c1.reason_codes
    assert "MASTERY_LOW" in eval_c1.reason_codes
    assert "RETENTION_LOW" in eval_c1.reason_codes

    # Daily Mission Deduplication
    mission = LearningPriorityEngine.generate_daily_mission([eval_c1, eval_c2, eval_c1], max_tasks=3)
    assert len(mission) == 2  # c1 duplicated must be deduplicated
    assert mission[0].concept_id == "c-recursion"


# =========================================================================
# 2. Database Integration & Workflow Lifecycle Tests
# =========================================================================

@pytest.mark.asyncio
async def test_knowledge_state_evidence_ingestion_and_rebuild_lifecycle(db_session: AsyncSession):
    """End-to-end integration test verifying evidence ingestion, idempotency, SM-2 review, and rebuild."""
    clock = FrozenClock(datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc))
    service = KnowledgeStateService(clock=clock)

    # 1. Setup Academic & Canonical Entities
    inst = Institution(name="National Institute of Technology", code=f"NIT_{uuid.uuid4().hex[:6]}")
    dept = Department(institution=inst, name="Computer Science", code=f"CSE_{uuid.uuid4().hex[:4]}")
    db_session.add_all([inst, dept])
    await db_session.flush()

    prog = Program(department_id=dept.id, name="B.Tech Computer Science", code=f"CS_{uuid.uuid4().hex[:4]}", degree_type="Bachelor")
    ay = AcademicYear(institution_id=inst.id, name="2026-2027", start_date=datetime(2026, 8, 1).date(), end_date=datetime(2027, 5, 31).date())
    db_session.add_all([prog, ay])
    await db_session.flush()

    batch = Batch(institution_id=inst.id, program_id=prog.id, admission_year=2026, graduation_year=2030, label="2026-2030")
    sem = Semester(academic_year_id=ay.id, semester_number=1, label="Semester 1", start_date=datetime(2026, 8, 1).date(), end_date=datetime(2026, 12, 31).date())
    db_session.add_all([batch, sem])
    await db_session.flush()

    sec = Section(batch_id=batch.id, name="Section A", capacity=60)
    db_session.add(sec)
    await db_session.flush()

    student_user = User(
        email=f"student_{uuid.uuid4().hex[:6]}@nit.edu",
        normalized_email=f"student_{uuid.uuid4().hex[:6]}@nit.edu",
        first_name="Rohan",
        last_name="Sharma",
        display_name="Rohan Sharma",
        role="student",
        institution_id=inst.id,
        hashed_password="hash",
    )
    db_session.add(student_user)
    await db_session.flush()

    student_prof = StudentAcademicProfile(
        user_id=student_user.id,
        institution_id=inst.id,
        program_id=prog.id,
        batch_id=batch.id,
        current_section_id=sec.id,
        enrollment_number=f"NIT_{uuid.uuid4().hex[:6].upper()}",
        admission_year=2026,
        graduation_year=2030,
    )
    db_session.add(student_prof)
    await db_session.flush()

    # Canonical Concept
    concept = Concept(
        name=f"Binary Search Algorithm {uuid.uuid4().hex[:4]}",
        slug=f"binary-search-{uuid.uuid4().hex[:4]}",
        difficulty="intermediate",
    )
    db_session.add(concept)
    await db_session.flush()

    # Question Bank & Version
    qbank = QuestionBank(
        institution_id=inst.id,
        title="Algorithms Core Bank",
    )
    db_session.add(qbank)
    await db_session.flush()

    question = Question(
        bank_id=qbank.id,
        title="Binary Search Complexity",
        question_type="single_choice",
        status="approved",
    )
    db_session.add(question)
    await db_session.flush()

    q_ver = QuestionVersion(
        question_id=question.id,
        version_number=1,
        prompt="What is the worst-case time complexity of binary search?",
        difficulty="medium",
        points=Decimal("2.0"),
    )
    db_session.add(q_ver)
    await db_session.flush()

    # 2. Emit Domain 5 ConceptEvidence record (Score: 1.0000)
    ev1 = ConceptEvidence(
        student_profile_id=student_prof.id,
        concept_id=concept.id,
        question_version_id=q_ver.id,
        score=Decimal("1.0000"),
        max_score=Decimal("1.0000"),
        evidence_type="assessment",
        timestamp=clock.now(),
    )
    db_session.add(ev1)
    await db_session.commit()

    # 3. Ingest First Evidence
    k_state_1 = await service.ingest_concept_evidence(db_session, ev1.id)
    assert k_state_1 is not None
    assert k_state_1.student_profile_id == student_prof.id
    assert k_state_1.concept_id == concept.id
    assert k_state_1.evidence_count == 1
    assert k_state_1.state == "introduced"

    # 4. Test Idempotency: Processing same evidence again must not duplicate or alter state
    k_state_dup = await service.ingest_concept_evidence(db_session, ev1.id)
    assert k_state_dup is not None
    assert k_state_dup.id == k_state_1.id
    assert k_state_dup.evidence_count == 1

    # 5. Ingest Second Evidence (Score: 0.9000)
    clock.advance(days=1)
    ev2 = ConceptEvidence(
        student_profile_id=student_prof.id,
        concept_id=concept.id,
        question_version_id=q_ver.id,
        score=Decimal("0.9000"),
        max_score=Decimal("1.0000"),
        evidence_type="assessment",
        timestamp=clock.now(),
    )
    db_session.add(ev2)
    await db_session.commit()

    k_state_2 = await service.ingest_concept_evidence(db_session, ev2.id)
    assert k_state_2 is not None
    assert k_state_2.evidence_count == 2
    assert k_state_2.current_mastery is not None
    assert k_state_2.current_mastery >= Decimal("0.8500")

    # 6. Verify SM-2 Review State was initialized
    review_stmt = select(ConceptReviewState).where(
        and_(
            ConceptReviewState.student_profile_id == student_prof.id,
            ConceptReviewState.concept_id == concept.id,
        )
    )
    r_state = (await db_session.execute(review_stmt)).scalar_one_or_none()
    assert r_state is not None
    assert r_state.repetition == 0
    assert r_state.interval_days == 1

    # 7. Time Travel: Advance clock by 2 days -> Review becomes due
    clock.advance(days=2)
    due_reviews = await service.get_due_reviews(db_session, student_prof.id)
    assert len(due_reviews) >= 1
    assert due_reviews[0].concept_id == concept.id

    # 8. Complete Review with Quality 5 (flawless recall)
    updated_r, updated_k = await service.complete_concept_review(
        db_session,
        student_profile_id=student_prof.id,
        concept_id=concept.id,
        quality=5,
        duration_seconds=30,
    )
    assert updated_r.repetition == 1
    assert updated_r.last_quality == 5
    from app.domains.mastery.service import to_utc
    assert to_utc(updated_r.next_review_at) > to_utc(clock.now())

    # Verify review history log
    h_stmt = select(ConceptReviewHistory).where(
        ConceptReviewHistory.student_profile_id == student_prof.id
    )
    histories = (await db_session.execute(h_stmt)).scalars().all()
    assert len(histories) == 1
    assert histories[0].quality == 5

    # 9. Test Full Rebuild
    rebuilt_count = await service.rebuild_student_knowledge_state(db_session, student_prof.id)
    assert rebuilt_count >= 1

    # 10. Summary API verification
    summary = await service.get_student_knowledge_summary(db_session, student_prof.id)
    assert summary["total_concepts_tracked"] >= 1
    assert summary["average_mastery"] is not None


@pytest.mark.asyncio
async def test_knowledge_api_endpoints_and_security(async_client, db_session: AsyncSession):
    """Verifies REST API endpoints, review completion, and RBAC / institutional isolation."""
    from app.core.security import create_access_token, UserRole

    # Setup 2 institutions and users
    inst1 = Institution(name="Institute 1", code=f"I1_{uuid.uuid4().hex[:6]}")
    inst2 = Institution(name="Institute 2", code=f"I2_{uuid.uuid4().hex[:6]}")
    dept1 = Department(institution=inst1, name="CSE", code=f"D1_{uuid.uuid4().hex[:4]}")
    dept2 = Department(institution=inst2, name="ECE", code=f"D2_{uuid.uuid4().hex[:4]}")
    db_session.add_all([inst1, inst2, dept1, dept2])
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

    concept = Concept(name=f"Graphs {uuid.uuid4().hex[:4]}", slug=f"graphs-{uuid.uuid4().hex[:4]}", difficulty="hard")
    db_session.add(concept)
    await db_session.commit()

    token_stud1 = create_access_token(subject=stud1.id, role=UserRole.STUDENT, institution_id=inst1.id)
    token_stud2 = create_access_token(subject=stud2.id, role=UserRole.STUDENT, institution_id=inst2.id)
    token_teacher1 = create_access_token(subject=teacher1.id, role=UserRole.TEACHER, institution_id=inst1.id)

    client = async_client

    # 1. Student 1 Knowledge Summary
    resp = await client.get("/api/v1/knowledge/me", headers={"Authorization": f"Bearer {token_stud1}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_concepts_tracked"] == 0

    # 2. Student 2 cannot access faculty/admin endpoint for student 1
    resp_cross = await client.get(f"/api/v1/students/{prof1.id}/knowledge", headers={"Authorization": f"Bearer {token_stud2}"})
    assert resp_cross.status_code == 403

    # 3. Teacher 1 from Inst 1 can access student 1 from Inst 1
    resp_teach = await client.get(f"/api/v1/students/{prof1.id}/knowledge", headers={"Authorization": f"Bearer {token_teacher1}"})
    assert resp_teach.status_code == 200

    # 4. Teacher 1 from Inst 1 CANNOT access student 2 from Inst 2 (Institutional Boundary)
    resp_cross_inst = await client.get(f"/api/v1/students/{prof2.id}/knowledge", headers={"Authorization": f"Bearer {token_teacher1}"})
    assert resp_cross_inst.status_code == 403

    # 5. Spaced Repetition Review Completion via API
    rev_resp = await client.post(
        f"/api/v1/reviews/{concept.id}/complete",
        headers={"Authorization": f"Bearer {token_stud1}"},
        json={"quality": 4, "duration_seconds": 45},
    )
    assert rev_resp.status_code == 200
    rev_data = rev_resp.json()
    assert rev_data["last_quality"] == 4
    assert rev_data["repetition"] == 1

    # 6. Verify Daily Mission API returns structured tasks
    mission_resp = await client.get("/api/v1/learning-priority/me/daily", headers={"Authorization": f"Bearer {token_stud1}"})
    assert mission_resp.status_code == 200
    mission_data = mission_resp.json()
    assert "tasks" in mission_data
    assert "date" in mission_data
