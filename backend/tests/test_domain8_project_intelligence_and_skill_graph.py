"""Tests for Domain 8: Project Intelligence, Evidence Graph & Portfolio Engine."""

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
    StudentPortfolio,
    StudentCertification,
    StudentAchievement,
)
from app.domains.content.models import Concept, ConceptSkill
from app.domains.project_intelligence.models import (
    ProjectConcept,
    ProjectEvidence,
    ProjectReview,
    PortfolioIntelligenceSnapshot,
)
from app.domains.project_intelligence.quality_engine import (
    ProjectQualityEngine,
    ProjectQualityInput,
)
from app.domains.project_intelligence.relevance_engine import (
    CareerRelevanceEngine,
    CareerSkillRequirementItem,
)
from app.domains.project_intelligence.portfolio_engine import (
    PortfolioIntelligenceEngine,
    PortfolioEvaluationInput,
    ProjectSummaryItem,
)
from app.domains.project_intelligence.providers import (
    DefaultRepositoryProvider,
)
from app.domains.project_intelligence.service import project_intelligence_service
from app.domains.project_intelligence.graph_service import skill_graph_service


async def _create_test_student(db_session: AsyncSession, tag: str, first_name="Arjun", last_name="Rao"):
    """Helper to provision a complete, valid student with institutional context."""
    now = datetime.now(timezone.utc)
    inst = Institution(name=f"College of Engineering {tag}", code=f"INST_{tag}", status="active")
    db_session.add(inst)
    await db_session.flush()

    dept = Department(name=f"Computer Science {tag}", code=f"DEPT_{tag}", institution_id=inst.id, status="active")
    db_session.add(dept)
    await db_session.flush()

    prog = Program(
        name=f"B.Tech CSE {tag}",
        code=f"PROG_{tag}",
        department_id=dept.id,
        degree_type="B.Tech",
        duration_years=4,
        status="active",
    )
    db_session.add(prog)
    await db_session.flush()

    batch = Batch(
        institution_id=inst.id,
        program_id=prog.id,
        admission_year=2026,
        graduation_year=2030,
        label=f"2026-2030 {tag}",
        status="active",
    )
    db_session.add(batch)
    await db_session.flush()

    user = User(
        email=f"student_{tag}@domain8.edu",
        normalized_email=f"student_{tag}@domain8.edu",
        hashed_password="hashed_test_password",
        role=UserRole.STUDENT,
        first_name=first_name,
        last_name=last_name,
        display_name=f"{first_name} {last_name}",
        institution_id=inst.id,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add(user)
    await db_session.flush()

    prof = StudentAcademicProfile(
        user_id=user.id,
        institution_id=inst.id,
        program_id=prog.id,
        batch_id=batch.id,
        enrollment_number=f"ENR_{tag}",
        admission_year=2026,
        graduation_year=2030,
        academic_status="active",
        created_at=now,
        updated_at=now,
    )
    db_session.add(prof)
    await db_session.flush()

    return user, prof, inst


# =========================================================================
# 1. Pure Deterministic Engine Tests
# =========================================================================

def test_pure_project_quality_engine_minimal_vs_complete():
    engine = ProjectQualityEngine()

    # Minimal / empty project
    min_input = ProjectQualityInput(
        title="My Project",
        status="in_progress",
    )
    min_res = engine.evaluate_project(min_input)
    assert min_res.algorithm_version == "v1.0.0-deterministic"
    assert min_res.overall_score < 40.0
    assert "technical_depth" in min_res.dimension_breakdown
    assert len(min_res.missing_elements) > 0

    # Comprehensive / verified project
    comp_input = ProjectQualityInput(
        title="Dhruva Full Stack Learning Platform",
        description="Comprehensive learning management platform with deterministic AI evidence graph and microservices.",
        problem_statement="Students lack verifiable evidence for their skill claims during placement interviews.",
        solution="Built an auditable graph linking concepts, courses, assessments and projects directly to career catalogs.",
        technologies=["Python", "FastAPI", "React", "TypeScript", "PostgreSQL", "Docker"],
        status="completed",
        repository_url="https://github.com/dhruva-ai/core-engine",
        live_url="https://dhruva.ai",
        documentation_url="https://docs.dhruva.ai",
        demo_url="https://demo.dhruva.ai",
        modules_contributed=["Auth Module", "Evidence Graph Engine", "REST API", "Database Layer"],
        skills_count=6,
        concepts_count=8,
        evidence_items_count=5,
        verified_evidence_count=4,
        has_test_evidence=True,
        has_architecture_diagram=True,
        faculty_review_score=92.0,
        faculty_review_breakdown={"technical_depth": 90.0, "code_quality": 95.0, "testing_quality": 90.0},
        is_verified=True,
    )
    comp_res = engine.evaluate_project(comp_input)
    assert comp_res.overall_score >= 85.0
    assert comp_res.technical_depth >= 80.0
    assert comp_res.documentation_quality >= 80.0
    assert comp_res.testing_quality >= 80.0
    assert comp_res.verification_strength >= 90.0


def test_pure_career_relevance_engine():
    engine = CareerRelevanceEngine()

    reqs = [
        CareerSkillRequirementItem(skill_id="s1", skill_name="React", importance="critical", weight=1.0),
        CareerSkillRequirementItem(skill_id="s2", skill_name="TypeScript", importance="critical", weight=0.9),
        CareerSkillRequirementItem(skill_id="s3", skill_name="Node.js", importance="important", weight=0.8),
        CareerSkillRequirementItem(skill_id="s4", skill_name="CSS", importance="nice_to_have", weight=0.5),
    ]

    # Project covering all critical skills
    res_high = engine.evaluate_relevance(
        project_id="p1",
        project_title="Full Stack React App",
        project_skill_ids=["s1", "s2", "s3"],
        project_skill_names={"s1": "React", "s2": "TypeScript", "s3": "Node.js"},
        career_id="c1",
        career_title="Frontend Engineer",
        career_requirements=reqs,
    )
    assert res_high.relevance_tier == "high"
    assert res_high.relevance_score >= 70.0
    assert len(res_high.critical_matches) == 2

    # Project with zero overlap
    res_none = engine.evaluate_relevance(
        project_id="p2",
        project_title="Data Analysis in R",
        project_skill_ids=["s99"],
        project_skill_names={"s99": "R Lang"},
        career_id="c1",
        career_title="Frontend Engineer",
        career_requirements=reqs,
    )
    assert res_none.relevance_tier == "none"
    assert res_none.relevance_score == 0.0
    assert len(res_none.remaining_career_gaps) >= 2


def test_pure_portfolio_engine_insufficient_vs_healthy():
    engine = PortfolioIntelligenceEngine()

    # Rule: If no projects and no skills, status must be insufficient_evidence
    empty_input = PortfolioEvaluationInput(
        has_portfolio_record=True,
        projects=[],
        total_skills_count=0,
        verified_skills_count=0,
    )
    empty_res = engine.evaluate_portfolio(empty_input)
    assert empty_res.status == "insufficient_evidence"
    assert empty_res.overall_health_score is None
    assert any("project" in s.lower() for s in empty_res.missing_sections)
    assert any("skill" in s.lower() for s in empty_res.missing_sections)

    # Healthy portfolio
    healthy_input = PortfolioEvaluationInput(
        has_portfolio_record=True,
        headline="Aspiring Cloud Solutions Architect",
        bio="Passionate engineer building scalable distributed architectures and verifiable systems.",
        contact_email="engineer@dhruva.ai",
        social_links_count=3,
        custom_links_count=1,
        public_visibility=True,
        projects=[
            ProjectSummaryItem(
                id="p1",
                title="Distributed KV Store",
                project_type="capstone",
                status="completed",
                is_verified=True,
                quality_score=88.0,
                has_problem_and_solution=True,
                has_repo_or_demo=True,
                skills_count=4,
                evidence_count=3,
                is_career_aligned=True,
            ),
            ProjectSummaryItem(
                id="p2",
                title="Cloud Monitoring Agent",
                project_type="open_source",
                status="completed",
                is_verified=True,
                quality_score=82.0,
                has_problem_and_solution=True,
                has_repo_or_demo=True,
                skills_count=3,
                evidence_count=2,
                is_career_aligned=True,
            ),
        ],
        total_skills_count=8,
        verified_skills_count=6,
        total_certifications_count=2,
        verified_certifications_count=2,
        total_achievements_count=1,
        has_career_goal=True,
    )
    healthy_res = engine.evaluate_portfolio(healthy_input)
    assert healthy_res.status == "assessed"
    assert healthy_res.overall_health_score is not None
    assert healthy_res.overall_health_score >= 70.0
    assert healthy_res.completeness_score >= 80.0
    assert healthy_res.technical_depth >= 75.0


def test_pure_repository_provider():
    provider = DefaultRepositoryProvider()

    # GitHub
    gh = provider.parse_repository_url("https://github.com/Dhruva-AI/dhruva-core.git")
    assert gh is not None
    assert gh.provider == "github"
    assert gh.owner == "Dhruva-AI"
    assert gh.repo_name == "dhruva-core"
    assert gh.normalized_url == "https://github.com/Dhruva-AI/dhruva-core"

    # GitLab
    gl = provider.parse_repository_url("https://gitlab.com/college-lab/semester-project")
    assert gl is not None
    assert gl.provider == "gitlab"

    # Invalid
    inv = provider.parse_repository_url("not_a_valid_url")
    assert inv is None


# =========================================================================
# 2. Database Integration & Security Tests
# =========================================================================

@pytest.mark.asyncio
async def test_project_lifecycle_crud_and_repository_evidence(db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    tag = uuid.uuid4().hex[:6]

    u, prof, inst = await _create_test_student(db_session, tag, "Arjun", "Rao")

    # Catalog Skill
    skill = SkillCatalog(
        name=f"React Framework {tag}",
        code=f"SK_REACT_{tag}",
        slug=f"react-{tag}",
        category="frontend",
        status="active",
        created_at=now,
        updated_at=now,
    )
    db_session.add(skill)
    await db_session.flush()

    # 1. Create Project
    proj_data = {
        "title": f"Healthcare Telemedicine Portal {tag}",
        "short_description": "Full-stack telemedicine video consultation platform.",
        "problem_statement": "Rural patients face long transit times to access specialized healthcare.",
        "solution": "WebRTC-based encrypted video consultation and prescription workflow.",
        "project_type": "capstone",
        "status": "completed",
        "technologies": ["React", "FastAPI", "WebRTC", "PostgreSQL"],
        "repository_url": "https://github.com/test-org/telemed-portal",
        "live_url": "https://telemed.test-org.org",
        "team_or_individual": "team",
        "team_size": 3,
        "role": "Frontend Lead",
        "contribution_description": "Implemented React consultation room and authentication UI.",
        "contribution_percentage": 40.0,
        "modules_contributed": ["Video Room", "Prescription Generator"],
        "visibility": "public",
        "skill_ids": [skill.id],
    }

    project = await project_intelligence_service.create_project(
        db=db_session,
        student_profile_id=prof.id,
        data=proj_data,
    )
    await db_session.commit()

    assert project.id is not None
    assert project.verification_status == "unverified"
    assert project.is_verified is False
    assert project.quality_score is not None

    # Verify repository evidence was automatically ingested
    stmt_ev = select(ProjectEvidence).where(ProjectEvidence.project_id == project.id)
    ev_items = (await db_session.execute(stmt_ev)).scalars().all()
    assert len(ev_items) == 1
    assert ev_items[0].evidence_type == "repository"
    assert ev_items[0].source == "github"

    # 2. Update Project
    upd_proj = await project_intelligence_service.update_project(
        db=db_session,
        project_id=project.id,
        student_profile_id=prof.id,
        data={"short_description": "Updated telemedicine consultation platform with chat."},
    )
    await db_session.commit()
    assert upd_proj.short_description == "Updated telemedicine consultation platform with chat."


@pytest.mark.asyncio
async def test_evidence_verification_and_unauthorized_self_verification_defense(db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    tag = uuid.uuid4().hex[:6]

    u_stud, prof, inst = await _create_test_student(db_session, tag, "Rohan", "Gupta")

    # Teacher User
    u_fac = User(
        email=f"f_{tag}@domain8.edu",
        normalized_email=f"f_{tag}@domain8.edu",
        hashed_password="pw",
        role=UserRole.TEACHER,
        first_name="Dr. Vikram",
        last_name="Sharma",
        display_name="Dr. Vikram Sharma",
        institution_id=inst.id,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add(u_fac)
    await db_session.flush()

    project = StudentProject(
        student_profile_id=prof.id,
        title=f"AI Attendance System {tag}",
        slug=f"ai-attendance-{tag}",
        status="completed",
        created_at=now,
        updated_at=now,
    )
    db_session.add(project)
    await db_session.flush()

    # Submit evidence
    ev = await project_intelligence_service.add_project_evidence(
        db=db_session,
        project_id=project.id,
        student_profile_id=prof.id,
        evidence_in={
            "evidence_type": "test_report",
            "source": "ci_pipeline",
            "source_reference": "https://ci.domain8.edu/build/9912",
            "title": "Automated Unit Test Coverage Report (89%)",
            "evidence_strength": 0.85,
        },
    )
    await db_session.commit()
    assert ev.verification_status == "submitted"

    # INVARIANT DEFENSE: Student cannot verify their own evidence!
    with pytest.raises(PermissionError, match="Students cannot verify their own evidence"):
        await project_intelligence_service.verify_project_evidence(
            db=db_session,
            evidence_id=ev.id,
            reviewer_user=u_stud,
            decision="verified",
        )

    # Faculty verifies evidence
    verified_ev = await project_intelligence_service.verify_project_evidence(
        db=db_session,
        evidence_id=ev.id,
        reviewer_user=u_fac,
        decision="verified",
        verification_notes="Verified against CI test run artifacts.",
    )
    await db_session.commit()
    assert verified_ev.verification_status == "verified"
    assert verified_ev.verified_by_user_id == u_fac.id


@pytest.mark.asyncio
async def test_faculty_review_rubric_and_domain7_bridge(db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    tag = uuid.uuid4().hex[:6]

    u_stud, prof, inst = await _create_test_student(db_session, tag, "Pooja", "Iyer")

    u_fac = User(
        email=f"fc_{tag}@domain8.edu",
        normalized_email=f"fc_{tag}@domain8.edu",
        hashed_password="pw",
        role=UserRole.TEACHER,
        first_name="Prof. Anand",
        last_name="Menon",
        display_name="Prof. Anand Menon",
        institution_id=inst.id,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add(u_fac)
    await db_session.flush()

    skill = SkillCatalog(
        name=f"FastAPI Backend {tag}",
        code=f"SK_FASTAPI_{tag}",
        slug=f"fastapi-{tag}",
        category="backend",
        status="active",
        created_at=now,
        updated_at=now,
    )
    db_session.add(skill)
    await db_session.flush()

    project = StudentProject(
        student_profile_id=prof.id,
        title=f"Microservices Banking Engine {tag}",
        slug=f"banking-engine-{tag}",
        status="completed",
        created_at=now,
        updated_at=now,
    )
    db_session.add(project)
    await db_session.flush()

    # Link skill to project
    ps = StudentProjectSkill(
        project_id=project.id,
        skill_catalog_id=skill.id,
        claimed_level="advanced",
        evidence_strength=0.7,
        verification_status="unverified",
        created_at=now,
    )
    db_session.add(ps)
    await db_session.flush()

    # INVARIANT DEFENSE: Student cannot self-review their own project!
    with pytest.raises(PermissionError, match="Students cannot review their own project"):
        await project_intelligence_service.submit_faculty_review(
            db=db_session,
            project_id=project.id,
            reviewer_user=u_stud,
            review_data={"technical_depth": 90.0},
        )

    # Faculty submits structured 10-dimension rubric review
    review = await project_intelligence_service.submit_faculty_review(
        db=db_session,
        project_id=project.id,
        reviewer_user=u_fac,
        review_data={
            "technical_depth": 88.0,
            "problem_solving": 85.0,
            "code_quality": 90.0,
            "architecture_quality": 92.0,
            "documentation_quality": 80.0,
            "testing_quality": 84.0,
            "practical_application": 90.0,
            "originality": 85.0,
            "student_contribution_score": 90.0,
            "professional_presentation": 86.0,
            "feedback": "Outstanding architectural separation and clean OpenAPI specification.",
            "decision": "approved",
        },
    )
    await db_session.commit()

    assert review.overall_score == 87.0
    assert review.is_finalized is True
    assert project.is_verified is True
    assert project.verification_status == "verified"
    assert project.verified_by_user_id == u_fac.id

    # Verify project skill was marked verified
    await db_session.refresh(ps)
    assert ps.verification_status == "verified"
    assert ps.verified_by_user_id == u_fac.id


@pytest.mark.asyncio
async def test_portfolio_builder_and_safe_public_view(db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    tag = uuid.uuid4().hex[:6]

    u, prof, inst = await _create_test_student(db_session, tag, "Kavya", "Nair")

    # Add verified skill
    sk = SkillCatalog(
        name=f"Go Systems {tag}",
        code=f"SK_GO_{tag}",
        slug=f"go-{tag}",
        category="systems",
        status="active",
        created_at=now,
        updated_at=now,
    )
    db_session.add(sk)
    await db_session.flush()

    stud_sk = StudentSkill(
        student_profile_id=prof.id,
        skill_catalog_id=sk.id,
        proficiency="advanced",
        is_verified=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add(stud_sk)

    # Add public project and private project
    p_pub = StudentProject(
        student_profile_id=prof.id,
        title="Public Distributed Cache",
        slug=f"dist-cache-{tag}",
        visibility="public",
        status="completed",
        is_verified=True,
        created_at=now,
        updated_at=now,
    )
    p_priv = StudentProject(
        student_profile_id=prof.id,
        title="Internal Draft Secret Project",
        slug=f"internal-secret-{tag}",
        visibility="private",
        status="draft",
        is_verified=False,
        created_at=now,
        updated_at=now,
    )
    db_session.add_all([p_pub, p_priv])
    await db_session.flush()

    # 1. Update Portfolio (turn on public visibility)
    port = await project_intelligence_service.update_portfolio(
        db=db_session,
        student_profile_id=prof.id,
        data={
            "slug": f"kavya-{tag}",
            "headline": "Distributed Systems Engineer",
            "bio": "Building high-throughput concurrent software.",
            "public_visibility": True,
            "contact_email": f"kavya_{tag}@work.io",
        },
    )
    await db_session.commit()
    assert port.public_visibility is True

    # 2. Evaluate Portfolio Health
    health = await project_intelligence_service.evaluate_portfolio_health(db=db_session, student_profile_id=prof.id)
    assert health.algorithm_version == "v1.0.0-deterministic"
    assert health.status == "assessed"
    assert health.overall_health_score is not None

    # 3. Retrieve Public Portfolio View
    pub_data = await project_intelligence_service.get_public_portfolio(db=db_session, slug_or_username=f"kavya-{tag}")
    assert pub_data is not None
    assert pub_data["student_name"] == "Kavya Nair"
    assert pub_data["headline"] == "Distributed Systems Engineer"

    # CRITICAL LEAKAGE TEST: Only public projects must be present; private project must NEVER leak
    project_titles = [p["title"] for p in pub_data["projects"]]
    assert "Public Distributed Cache" in project_titles
    assert "Internal Draft Secret Project" not in project_titles


@pytest.mark.asyncio
async def test_skill_graph_service_relational_traversal(db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    tag = uuid.uuid4().hex[:6]

    u, prof, inst = await _create_test_student(db_session, tag, "Dev", "Patel")

    skill = SkillCatalog(
        name=f"Docker Containerization {tag}",
        code=f"SK_DOCKER_{tag}",
        slug=f"docker-{tag}",
        category="devops",
        status="active",
        created_at=now,
        updated_at=now,
    )
    career = CareerCatalog(
        title=f"DevOps Specialist {tag}",
        code=f"CAR_DEVOPS_{tag}",
        slug=f"devops-{tag}",
        industry="Technology",
        status="active",
        created_at=now,
        updated_at=now,
    )
    db_session.add_all([skill, career])
    await db_session.flush()

    # Career Skill Mapping
    csm = CareerSkillMapping(
        career_id=career.id,
        skill_id=skill.id,
        importance="critical",
        weight=Decimal("1.00"),
    )
    db_session.add(csm)

    # Project demonstrating Docker
    proj = StudentProject(
        student_profile_id=prof.id,
        title=f"Multi-container Deployment {tag}",
        slug=f"multi-container-{tag}",
        status="completed",
        is_verified=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add(proj)
    await db_session.flush()

    ps = StudentProjectSkill(
        project_id=proj.id,
        skill_catalog_id=skill.id,
        claimed_level="advanced",
        verification_status="verified",
        created_at=now,
    )
    db_session.add(ps)

    ev = ProjectEvidence(
        project_id=proj.id,
        student_profile_id=prof.id,
        evidence_type="deployment",
        source="docker_hub",
        source_reference="docker.io/test/demo",
        title="Production Container Image",
        submitted_at=now,
        verification_status="verified",
        evidence_strength=0.9,
    )
    db_session.add(ev)
    await db_session.commit()

    # Query Skill Evidence Graph
    graph_res = await skill_graph_service.get_skill_evidence_graph(
        db=db_session,
        skill_id=skill.id,
        student_profile_id=prof.id,
    )
    assert graph_res["skill_id"] == skill.id
    assert graph_res["provenance_summary"]["projects_count"] == 1
    assert graph_res["provenance_summary"]["verified_projects_count"] == 1
    assert len(graph_res["projects"]) == 1
    assert len(graph_res["project_evidence"]) == 1
    assert len(graph_res["target_careers"]) == 1
    assert graph_res["target_careers"][0]["career_title"] == career.title


# =========================================================================
# 3. HTTP REST API Endpoint Tests
# =========================================================================

@pytest.mark.asyncio
async def test_http_api_endpoints_domain8(async_client: AsyncClient, db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    tag = uuid.uuid4().hex[:6]

    u_stud, prof, inst = await _create_test_student(db_session, tag, "Rishi", "Sen")

    # Teacher User
    u_fac = User(
        email=f"api_f_{tag}@domain8.edu",
        normalized_email=f"api_f_{tag}@domain8.edu",
        hashed_password="pw",
        role=UserRole.TEACHER,
        first_name="Dr. Nita",
        last_name="Roy",
        display_name="Dr. Nita Roy",
        institution_id=inst.id,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add(u_fac)

    sk = SkillCatalog(
        name=f"GraphQL APIs {tag}",
        code=f"SK_GQL_{tag}",
        slug=f"gql-{tag}",
        category="api",
        status="active",
        created_at=now,
        updated_at=now,
    )
    db_session.add(sk)
    await db_session.commit()

    token_stud = create_access_token(subject=u_stud.id, role=u_stud.role)
    token_fac = create_access_token(subject=u_fac.id, role=u_fac.role)
    headers_stud = {"Authorization": f"Bearer {token_stud}"}
    headers_fac = {"Authorization": f"Bearer {token_fac}"}

    # 1. POST /api/v1/projects
    p_resp = await async_client.post(
        "/api/v1/projects",
        json={
            "title": f"Federated GraphQL Gateway {tag}",
            "description": "High performance Apollo gateway combining subgraphs.",
            "problem_statement": "Microservices client applications suffered from multiple REST round-trips.",
            "solution": "Unified supergraph schema with sub-millisecond query planning.",
            "project_type": "academic",
            "status": "completed",
            "technologies": ["GraphQL", "Node.js", "TypeScript"],
            "repository_url": "https://github.com/org/supergraph",
            "visibility": "public",
            "skill_ids": [sk.id],
        },
        headers=headers_stud,
    )
    assert p_resp.status_code == 201, p_resp.text
    p_data = p_resp.json()
    project_id = p_data["id"]
    assert p_data["title"] == f"Federated GraphQL Gateway {tag}"

    # 2. GET /api/v1/projects
    list_resp = await async_client.get("/api/v1/projects", headers=headers_stud)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # 3. GET /api/v1/projects/{id}
    detail_resp = await async_client.get(f"/api/v1/projects/{project_id}", headers=headers_stud)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == project_id

    # 4. GET /api/v1/projects/{id}/quality
    q_resp = await async_client.get(f"/api/v1/projects/{project_id}/quality", headers=headers_stud)
    assert q_resp.status_code == 200
    assert "overall_score" in q_resp.json()
    assert q_resp.json()["algorithm_version"] == "v1.0.0-deterministic"

    # 5. POST /api/v1/projects/{id}/evidence
    ev_resp = await async_client.post(
        f"/api/v1/projects/{project_id}/evidence",
        json={
            "evidence_type": "documentation",
            "source": "notion",
            "source_reference": "https://notion.so/docs/supergraph",
            "title": "Supergraph Architecture Specification",
            "evidence_strength": 0.8,
        },
        headers=headers_stud,
    )
    assert ev_resp.status_code == 201
    evidence_id = ev_resp.json()["id"]

    # 6. POST verify evidence - unauthorized for student
    self_verify_resp = await async_client.post(
        f"/api/v1/projects/{project_id}/evidence/{evidence_id}/verify",
        json={"decision": "verified"},
        headers=headers_stud,
    )
    assert self_verify_resp.status_code == 403

    # 7. POST verify evidence - authorized for faculty
    fac_verify_resp = await async_client.post(
        f"/api/v1/projects/{project_id}/evidence/{evidence_id}/verify",
        json={"decision": "verified", "verification_notes": "Architecture docs verified."},
        headers=headers_fac,
    )
    assert fac_verify_resp.status_code == 200
    assert fac_verify_resp.json()["verification_status"] == "verified"

    # 8. POST faculty review
    review_resp = await async_client.post(
        f"/api/v1/projects/{project_id}/reviews",
        json={
            "technical_depth": 85.0,
            "problem_solving": 80.0,
            "code_quality": 88.0,
            "architecture_quality": 90.0,
            "documentation_quality": 85.0,
            "testing_quality": 82.0,
            "practical_application": 85.0,
            "originality": 80.0,
            "student_contribution_score": 88.0,
            "professional_presentation": 85.0,
            "feedback": "Thoroughly planned supergraph with clear subgraphs.",
            "decision": "approved",
        },
        headers=headers_fac,
    )
    assert review_resp.status_code == 201
    assert review_resp.json()["decision"] == "approved"

    # 9. GET /api/v1/portfolio
    port_get = await async_client.get("/api/v1/portfolio", headers=headers_stud)
    assert port_get.status_code == 200

    # 10. PATCH /api/v1/portfolio
    port_patch = await async_client.patch(
        "/api/v1/portfolio",
        json={"headline": "GraphQL Architect", "public_visibility": True, "slug": f"rishi-{tag}"},
        headers=headers_stud,
    )
    assert port_patch.status_code == 200
    assert port_patch.json()["headline"] == "GraphQL Architect"

    # 11. GET /api/v1/portfolio/health
    health_resp = await async_client.get("/api/v1/portfolio/health", headers=headers_stud)
    assert health_resp.status_code == 200
    assert "overall_health_score" in health_resp.json()

    # 12. GET /api/v1/portfolio/public/{slug}
    pub_resp = await async_client.get(f"/api/v1/portfolio/public/rishi-{tag}")
    assert pub_resp.status_code == 200
    assert pub_resp.json()["student_name"] == "Rishi Sen"

    # 13. GET /api/v1/skills/{skill_id}/graph
    graph_resp = await async_client.get(f"/api/v1/skills/{sk.id}/graph", headers=headers_stud)
    assert graph_resp.status_code == 200
    assert graph_resp.json()["skill_id"] == sk.id
    assert "provenance_summary" in graph_resp.json()
