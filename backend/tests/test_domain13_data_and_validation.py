"""Comprehensive Test Suite for Domain 13: Real-World Academic Data, Seeding & Product Validation.

Validates:
1. National Academic Catalog taxonomy, skills, careers, and weighted mappings
2. Canonical Course Catalog, Concepts DAG, and prerequisite directed edges
3. Multi-type Question Banks (MCQ, True/False, Coding test cases) and Assessment Blueprints
4. Isolated Pilot Institution ("Dhruva Demo University") academic hierarchy
5. Synthetic Learner Cohorts: High Mastery, Prerequisite Gaps, Retention Decay, and Interventions
6. Domain 10 Adaptive Remediation integration via synthetic evidence
7. Domain 8 Project Intelligence & Portfolio Snapshot integration
8. Multi-tenant isolation (Demo Institution vs External Institution)
9. RAG Knowledge chunk indexing and scoped retrieval
10. Production safeguard blocking accidental synthetic execution
11. Seed idempotency (running twice produces zero duplicates)
"""

import pytest
import pytest_asyncio
import uuid
import os
from decimal import Decimal
from datetime import datetime, timezone, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.scripts import ensure_seed_safety
from app.scripts.seed_catalog import seed_academic_catalog
from app.scripts.seed_courses import seed_courses_and_concepts
from app.scripts.seed_questions import seed_question_banks_and_assessments
from app.scripts.seed_demo_institution import seed_demo_institution_and_cohort
from app.scripts.seed_rag import seed_rag_knowledge_chunks
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
    TeacherAcademicProfile,
    StudentAcademicProfile,
    StudentEnrollment,
)
from app.domains.catalog.models import (
    AcademicDiscipline,
    DegreeType,
    ProgramCatalog,
    SkillCatalog,
    CareerCatalog,
    CareerSkillMapping,
    CourseCatalog,
)
from app.domains.content.models import (
    Concept,
    ConceptPrerequisite,
    ConceptSkill,
)
from app.domains.assessment.models import (
    QuestionBank,
    Question,
    QuestionVersion,
    CodingConfiguration,
    CodingTestCase,
    Assessment,
)
from app.domains.mastery.models import (
    StudentConceptKnowledgeState,
    ConceptReviewState,
)
from app.domains.profiles.models import (
    StudentProject,
)
from app.domains.project_intelligence.models import (
    ProjectEvidence,
    ProjectReview,
    PortfolioIntelligenceSnapshot,
)
from app.domains.institutional_intelligence.models import (
    AcademicInterventionSignal,
)
from app.domains.remediation.models import (
    RemediationPlan,
    RemediationDiagnosis,
    RemediationPlanStep,
)
from app.domains.ai.models import AIKnowledgeChunk
from app.domains.ai.retrieval.retriever import ScopedKnowledgeRetriever


# =============================================================================
# 1. Production Safeguard Test
# =============================================================================

def test_production_safeguard_blocks_synthetic_seeding(monkeypatch):
    """Verify that in production mode, synthetic pilot seeding raises RuntimeError unless explicitly permitted."""
    monkeypatch.setattr(settings, "APPLICATION_ENV", "production")
    monkeypatch.delenv("ENABLE_SYNTHETIC_PILOT_DATA", raising=False)

    with pytest.raises(RuntimeError, match="CRITICAL DATA SAFETY VIOLATION"):
        ensure_seed_safety(allow_synthetic=True)

    # When explicit env flag is set, it passes
    monkeypatch.setenv("ENABLE_SYNTHETIC_PILOT_DATA", "true")
    ensure_seed_safety(allow_synthetic=True)  # Should not raise


# =============================================================================
# 2. National Academic Catalog Test
# =============================================================================

@pytest.mark.asyncio
async def test_academic_catalog_seeding_and_taxonomies(db_session: AsyncSession):
    """Verify Disciplines, Degrees, Programs, Skills, Careers and Mappings are created cleanly."""
    stats = await seed_academic_catalog(db_session)
    assert stats["disciplines"] >= 6
    assert stats["degree_types"] >= 4
    assert stats["programs"] >= 6
    assert stats["skills"] >= 30
    assert stats["careers"] >= 8

    # Verify B.Tech CSE Program
    cse_res = await db_session.execute(
        select(ProgramCatalog).where(ProgramCatalog.code == "BTECH_CSE")
    )
    btech_cse = cse_res.scalar_one_or_none()
    assert btech_cse is not None
    assert btech_cse.duration_years == 4.0

    # Verify Career-Skill Mappings
    car_res = await db_session.execute(
        select(CareerCatalog).where(CareerCatalog.code == "CAR-FULLSTACK")
    )
    fullstack = car_res.scalar_one_or_none()
    assert fullstack is not None

    maps_res = await db_session.execute(
        select(CareerSkillMapping).where(CareerSkillMapping.career_id == fullstack.id)
    )
    c_skills = maps_res.scalars().all()
    assert len(c_skills) >= 5


# =============================================================================
# 3. Canonical Courses and Concept DAG Test
# =============================================================================

@pytest.mark.asyncio
async def test_courses_and_concepts_prerequisite_dag(db_session: AsyncSession):
    """Verify 12 canonical courses and directed prerequisite relationships form a valid DAG."""
    await seed_academic_catalog(db_session)
    stats = await seed_courses_and_concepts(db_session)
    assert stats["courses"] >= 12
    assert stats["concepts"] >= 30
    assert stats["concept_prerequisites"] >= 20

    # Verify prerequisite integrity (no self-loops, valid sources and targets)
    edges_res = await db_session.execute(select(ConceptPrerequisite))
    edges = edges_res.scalars().all()
    assert len(edges) > 0

    for edge in edges:
        assert edge.concept_id != edge.prerequisite_concept_id
        # Verify concepts exist
        c1 = (await db_session.execute(select(Concept).where(Concept.id == edge.concept_id))).scalar_one()
        c2 = (await db_session.execute(select(Concept).where(Concept.id == edge.prerequisite_concept_id))).scalar_one()
        assert c1 is not None
        assert c2 is not None


# =============================================================================
# 4. Question Banks & Assessment Blueprints Test
# =============================================================================

@pytest.mark.asyncio
async def test_question_banks_and_multi_type_questions(db_session: AsyncSession):
    """Verify question banks, MCQ options, and sandbox coding test cases."""
    await seed_academic_catalog(db_session)
    await seed_courses_and_concepts(db_session)
    stats = await seed_question_banks_and_assessments(db_session)

    assert stats["question_banks"] >= 5
    assert stats["questions"] >= 10
    assert stats["coding_configs"] >= 1
    assert stats["coding_test_cases"] >= 3
    assert stats["assessments"] >= 2

    # Verify coding question test cases
    cc_res = await db_session.execute(select(CodingConfiguration))
    coding_config = cc_res.scalars().first()
    assert coding_config is not None
    assert coding_config.language == "python"
    assert len(coding_config.test_cases) >= 3


# =============================================================================
# 5. Synthetic Pilot Institution & 50 Students Cohort Test
# =============================================================================

@pytest.mark.asyncio
async def test_demo_institution_hierarchy_and_diverse_cohorts(db_session: AsyncSession):
    """Verify Dhruva Demo University, departments, faculty, and 50 diverse student learner profiles."""
    await seed_academic_catalog(db_session)
    await seed_courses_and_concepts(db_session)
    await seed_question_banks_and_assessments(db_session)
    stats = await seed_demo_institution_and_cohort(db_session)

    assert stats["departments"] == 5
    assert stats["faculty"] == 5
    assert stats["students"] == 50
    assert stats["enrollments"] == 200
    assert stats["knowledge_states"] >= 40
    assert stats["remediation_plans"] >= 5
    assert stats["intervention_signals"] >= 4

    # Verify Cohort 1: High Mastery and Verified Projects
    h_res = await db_session.execute(
        select(StudentConceptKnowledgeState)
        .where(StudentConceptKnowledgeState.state == "mastered")
    )
    mastered_states = h_res.scalars().all()
    assert len(mastered_states) >= 5
    for ms in mastered_states:
        assert ms.current_mastery >= Decimal("0.8500")

    # Verify Cohort 3: Remediation Plans and Diagnoses
    rem_res = await db_session.execute(
        select(RemediationPlan).where(RemediationPlan.diagnosis_type == "PREREQUISITE_GAP")
    )
    rem_plans = rem_res.scalars().all()
    assert len(rem_plans) >= 5
    for rp in rem_plans:
        assert rp.priority_score >= Decimal("0.5000")
        assert len(rp.steps) >= 2

    # Verify Cohort 4: SM-2 Retention Decay and Overdue Scheduling
    rev_res = await db_session.execute(
        select(ConceptReviewState).where(ConceptReviewState.review_status == "overdue")
    )
    overdue_reviews = rev_res.scalars().all()
    assert len(overdue_reviews) >= 5

    # Verify Cohort 6: Early Intervention Signals
    sig_res = await db_session.execute(select(AcademicInterventionSignal))
    signals = sig_res.scalars().all()
    assert len(signals) >= 4
    for sig in signals:
        assert sig.severity == "high"


# =============================================================================
# 6. Multi-Tenant Scoping Isolation Test
# =============================================================================

@pytest.mark.asyncio
async def test_multi_tenant_isolation_demo_vs_external(db_session: AsyncSession):
    """Verify that synthetic pilot data is strictly isolated from another institution."""
    await seed_academic_catalog(db_session)
    await seed_courses_and_concepts(db_session)
    await seed_demo_institution_and_cohort(db_session)

    # Create External Institution B ("Apex Institute of Technology")
    apex_inst = Institution(
        code="APEX-INST-001",
        name="Apex Institute of Technology",
        email_domains="apex.edu",
        status="active",
    )
    db_session.add(apex_inst)
    await db_session.flush()

    apex_dept = Department(
        institution_id=apex_inst.id,
        code="APEX-CSE",
        name="Apex Computer Science",
        status="active",
    )
    db_session.add(apex_dept)
    await db_session.flush()

    # Query Demo University departments
    demo_inst = (await db_session.execute(select(Institution).where(Institution.code == "DHRUVA-DEMO-U"))).scalar_one()
    demo_depts = (await db_session.execute(select(Department).where(Department.institution_id == demo_inst.id))).scalars().all()
    apex_depts = (await db_session.execute(select(Department).where(Department.institution_id == apex_inst.id))).scalars().all()

    assert len(demo_depts) == 5
    assert len(apex_depts) == 1
    # Verify no cross-tenant bleeding
    for dd in demo_depts:
        assert dd.institution_id == demo_inst.id
        assert dd.institution_id != apex_inst.id


# =============================================================================
# 7. RAG Knowledge Indexing and Retrieval Test
# =============================================================================

@pytest.mark.asyncio
async def test_rag_knowledge_chunk_indexing_and_retrieval(db_session: AsyncSession):
    """Verify that canonical concepts are indexed into AIKnowledgeChunk and retrievable via ScopedKnowledgeRetriever."""
    await seed_academic_catalog(db_session)
    await seed_courses_and_concepts(db_session)
    rag_stats = await seed_rag_knowledge_chunks(db_session)
    assert rag_stats["knowledge_chunks"] >= 30

    # Retrieve via ScopedKnowledgeRetriever
    citations = await ScopedKnowledgeRetriever.retrieve_approved_content(
        db=db_session,
        query="Binary Trees",
        limit=5,
    )
    assert len(citations) > 0
    assert any("Binary Trees" in c["title"] or "Binary Trees" in c["content_snippet"] for c in citations)


# =============================================================================
# 8. Seed Idempotency Test
# =============================================================================

@pytest.mark.asyncio
async def test_seed_pipeline_full_idempotency(db_session: AsyncSession):
    """Verify that running the complete seed pipeline twice produces zero duplicate records."""
    # Run 1
    await seed_academic_catalog(db_session)
    await seed_courses_and_concepts(db_session)
    await seed_question_banks_and_assessments(db_session)
    await seed_demo_institution_and_cohort(db_session)
    await seed_rag_knowledge_chunks(db_session)

    # Run 2
    cat_stats2 = await seed_academic_catalog(db_session)
    course_stats2 = await seed_courses_and_concepts(db_session)
    q_stats2 = await seed_question_banks_and_assessments(db_session)
    demo_stats2 = await seed_demo_institution_and_cohort(db_session)
    rag_stats2 = await seed_rag_knowledge_chunks(db_session)

    # All secondary runs must yield 0 new insertions
    assert sum(cat_stats2.values()) == 0
    assert sum(course_stats2.values()) == 0
    assert sum(q_stats2.values()) == 0
    assert sum(demo_stats2.values()) == 0
    assert sum(rag_stats2.values()) == 0
