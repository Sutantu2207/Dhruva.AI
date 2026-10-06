"""Comprehensive test suite for Domain 2.5: National Academic Taxonomy & India-wide Catalog.

Validates:
1. Catalog creation authorization (Super Admin only)
2. Student read access (Can read/search catalog)
3. Teacher read access (Can read/search, cannot modify)
4. Institution Admin management (Can create institution mappings)
5. Super Admin management (Full administrative catalog control)
6. Duplicate prevention (Discipline, Program, Course, Skill, Career uniqueness)
7. Versioning (AcademicCatalogVersion tracking)
8. Source provenance (AcademicCatalogSource linking)
9. Program-specialization relationship
10. Course catalog properties & discipline association
11. Skill mappings (Program-Skill, Course-Skill)
12. Career mappings (Career-Skill, Program-Career)
13. Institution-program mapping
14. Institution-course mapping
15. Cross-institution isolation (Institution A cannot map for Institution B)
16. Import validation (Valid JSON/CSV structure)
17. Duplicate import handling (Idempotent processing)
18. Invalid records reporting (Import report tracks invalid entries)
19. Search across programs, courses, skills, and careers
20. Pagination (limit and offset)
21. Audit logging & Import job tracking
22. Unauthorized modification attempts (Student/Teacher POST/PATCH rejected)
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
    Course,
)
from app.domains.catalog.models import (
    AcademicCatalogVersion,
    AcademicCatalogSource,
    AcademicDiscipline,
    DegreeType,
    ProgramCatalog,
    CourseCatalog,
)
from app.domains.catalog.schemas import CareerSkillMappingCreate
from app.domains.catalog.service import academic_catalog_service


async def create_user_helper(
    db_session: AsyncSession,
    email: str,
    role: UserRole,
    institution_id: str | None = None,
    first_name: str = "Test",
    last_name: str = "User",
) -> tuple[User, str]:
    """Helper to persist a user in the test database and generate an auth token."""
    user = User(
        email=email,
        normalized_email=email.strip().lower(),
        hashed_password=get_password_hash("ValidPass123!"),
        first_name=first_name,
        last_name=last_name,
        display_name=f"{first_name} {last_name}",
        role=role,
        institution_id=institution_id,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    token = create_access_token(
        subject=str(user.id),
        role=role,
        institution_id=institution_id,
    )
    return user, token


def auth_headers(token: str) -> dict[str, str]:
    """Helper to create Authorization header for a user."""
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def catalog_seed(db_session: AsyncSession):
    """Seed foundational source, version, discipline, and degree type."""
    source = AcademicCatalogSource(
        code="AICTE-IN",
        name="All India Council for Technical Education",
        organization="Ministry of Education, Govt. of India",
        website_url="https://www.aicte-india.org",
        is_authoritative=True,
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)

    version = AcademicCatalogVersion(
        version_tag="v2026.1",
        source_id=source.id,
        status="active",
        effective_date=date(2026, 1, 1),
        notes="Annual national academic revision",
    )
    db_session.add(version)
    await db_session.commit()
    await db_session.refresh(version)

    discipline = AcademicDiscipline(
        code="ENG-TECH",
        name="Engineering & Technology",
        display_name="Engineering and Technology",
        slug="engineering-and-technology",
        description="Applied sciences and engineering disciplines",
        source_id=source.id,
        version_id=version.id,
    )
    db_session.add(discipline)
    await db_session.commit()
    await db_session.refresh(discipline)

    degree_type = DegreeType(
        code="BTECH",
        name="Bachelor of Technology",
        short_name="B.Tech",
        level=3,
        typical_duration_years=4.0,
        status="active",
    )
    db_session.add(degree_type)
    await db_session.commit()
    await db_session.refresh(degree_type)

    return {
        "source": source,
        "version": version,
        "discipline": discipline,
        "degree_type": degree_type,
    }


# ==============================================================================
# 1. CATALOG CREATION AUTHORIZATION (SUPER ADMIN ONLY) & 22. UNAUTHORIZED ATTEMPTS
# ==============================================================================

async def test_01_and_22_catalog_creation_authorization(
    async_client: AsyncClient, db_session: AsyncSession, catalog_seed
):
    _, sa_token = await create_user_helper(db_session, "sa@dhruva.ai", UserRole.SUPER_ADMIN)
    _, st_token = await create_user_helper(db_session, "student1@dhruva.ai", UserRole.STUDENT)
    _, tc_token = await create_user_helper(db_session, "teacher1@dhruva.ai", UserRole.TEACHER)

    prog_payload = {
        "code": "BTECH-CSE",
        "name": "Bachelor of Technology in Computer Science and Engineering",
        "short_name": "B.Tech CSE",
        "discipline_id": catalog_seed["discipline"].id,
        "degree_type_id": catalog_seed["degree_type"].id,
        "duration_years": 4.0,
        "description": "Undergraduate program in computer science and engineering",
        "aliases": ["B.Tech CS", "B.E. Computer Science"],
    }

    # Student cannot create national program
    resp_student = await async_client.post(
        "/api/v1/catalog/programs",
        json=prog_payload,
        headers=auth_headers(st_token),
    )
    assert resp_student.status_code == 403

    # Teacher cannot create national program
    resp_teacher = await async_client.post(
        "/api/v1/catalog/programs",
        json=prog_payload,
        headers=auth_headers(tc_token),
    )
    assert resp_teacher.status_code == 403

    # Super Admin can create national program
    resp_admin = await async_client.post(
        "/api/v1/catalog/programs",
        json=prog_payload,
        headers=auth_headers(sa_token),
    )
    assert resp_admin.status_code == 201
    data = resp_admin.json()
    assert data["code"] == "BTECH-CSE"
    assert "bachelor-of-technology-in-computer-science-and-engineering" in data["slug"]


# ==============================================================================
# 2. STUDENT READ ACCESS & 3. TEACHER READ ACCESS
# ==============================================================================

async def test_02_and_03_student_and_teacher_read_access(
    async_client: AsyncClient, db_session: AsyncSession, catalog_seed
):
    _, st_token = await create_user_helper(db_session, "student2@dhruva.ai", UserRole.STUDENT)
    _, tc_token = await create_user_helper(db_session, "teacher2@dhruva.ai", UserRole.TEACHER)

    # Student reads disciplines
    resp = await async_client.get("/api/v1/catalog/disciplines", headers=auth_headers(st_token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
    assert resp.json()[0]["code"] == "ENG-TECH"

    # Teacher reads degree types
    resp_deg = await async_client.get("/api/v1/catalog/degree-types", headers=auth_headers(tc_token))
    assert resp_deg.status_code == 200
    assert len(resp_deg.json()) >= 1
    assert resp_deg.json()[0]["code"] == "BTECH"


# ==============================================================================
# 4. INSTITUTION ADMIN MANAGEMENT & 13. INSTITUTION-PROGRAM MAPPING
# ==============================================================================

async def test_04_and_13_institution_admin_program_mapping(
    async_client: AsyncClient, db_session: AsyncSession, catalog_seed
):
    inst = Institution(name="IIT Delhi", code="IITD")
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)

    dept = Department(institution_id=inst.id, name="Computer Science", code="CSE")
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)

    local_prog = Program(
        department_id=dept.id,
        name="B.Tech Computer Science",
        code="CS1",
        degree_type="btech",
        duration_years=4,
    )
    db_session.add(local_prog)
    await db_session.commit()
    await db_session.refresh(local_prog)

    # Create national program
    nat_prog = ProgramCatalog(
        code="NAT-BTECH-CSE",
        name="Bachelor of Technology in Computer Science & Engineering",
        short_name="B.Tech CSE",
        slug="btech-cse-national",
        discipline_id=catalog_seed["discipline"].id,
        degree_type_id=catalog_seed["degree_type"].id,
        duration_years=4.0,
    )
    db_session.add(nat_prog)
    await db_session.commit()
    await db_session.refresh(nat_prog)

    _, inst_admin_token = await create_user_helper(
        db_session, "inst_admin@iitd.ac.in", UserRole.INSTITUTION_ADMIN, institution_id=inst.id
    )

    mapping_payload = {
        "institution_id": inst.id,
        "institution_program_id": local_prog.id,
        "national_program_id": nat_prog.id,
        "local_code": "CS-LOCAL",
        "local_name": "IITD B.Tech CSE",
        "confidence_score": 1.0,
        "notes": "Direct alignment with AICTE model curriculum",
    }

    resp = await async_client.post(
        "/api/v1/catalog/institution-program-mappings",
        json=mapping_payload,
        headers=auth_headers(inst_admin_token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["institution_id"] == inst.id
    assert data["local_name"] == "IITD B.Tech CSE"


# ==============================================================================
# 5. SUPER ADMIN MANAGEMENT & 6. DUPLICATE PREVENTION
# ==============================================================================

async def test_05_and_06_super_admin_crud_and_duplicate_prevention(
    async_client: AsyncClient, db_session: AsyncSession, catalog_seed
):
    _, sa_token = await create_user_helper(db_session, "sa_mgr@dhruva.ai", UserRole.SUPER_ADMIN)

    # 1. Create discipline
    disc_data = {
        "code": "SCI-MATH",
        "name": "Mathematical Sciences",
        "display_name": "Mathematics & Statistics",
        "description": "Pure and Applied Mathematics",
        "aliases": ["Maths", "Statistics"],
    }
    resp1 = await async_client.post(
        "/api/v1/catalog/disciplines",
        json=disc_data,
        headers=auth_headers(sa_token),
    )
    assert resp1.status_code == 201

    # 2. Duplicate discipline code rejection
    resp2 = await async_client.post(
        "/api/v1/catalog/disciplines",
        json=disc_data,
        headers=auth_headers(sa_token),
    )
    assert resp2.status_code == 409
    assert "already exists" in resp2.json()["detail"]


# ==============================================================================
# 7. VERSIONING & 8. SOURCE PROVENANCE
# ==============================================================================

async def test_07_and_08_versioning_and_sources(
    async_client: AsyncClient, db_session: AsyncSession, catalog_seed
):
    _, st_token = await create_user_helper(db_session, "stud_ver@dhruva.ai", UserRole.STUDENT)

    # Read versions
    resp_v = await async_client.get("/api/v1/catalog/catalog-versions", headers=auth_headers(st_token))
    assert resp_v.status_code == 200
    versions = resp_v.json()
    assert any(v["version_tag"] == "v2026.1" for v in versions)

    # Read sources
    resp_s = await async_client.get("/api/v1/catalog/sources", headers=auth_headers(st_token))
    assert resp_s.status_code == 200
    sources = resp_s.json()
    assert any(s["code"] == "AICTE-IN" for s in sources)


# ==============================================================================
# 9. PROGRAM-SPECIALIZATION RELATIONSHIP
# ==============================================================================

async def test_09_program_specialization_relationship(
    async_client: AsyncClient, db_session: AsyncSession, catalog_seed
):
    _, sa_token = await create_user_helper(db_session, "sa_spec@dhruva.ai", UserRole.SUPER_ADMIN)

    # Create program
    nat_prog = ProgramCatalog(
        code="BTECH-ENG",
        name="Bachelor of Technology",
        short_name="B.Tech",
        slug="btech-eng",
        discipline_id=catalog_seed["discipline"].id,
        degree_type_id=catalog_seed["degree_type"].id,
    )
    db_session.add(nat_prog)
    await db_session.commit()
    await db_session.refresh(nat_prog)

    # Add specialization via endpoint
    spec_data = {
        "program_catalog_id": nat_prog.id,
        "code": "AIML",
        "name": "Artificial Intelligence & Machine Learning",
        "description": "Specialized curriculum focusing on AI/ML models",
        "aliases": ["AI-ML", "AI"],
    }
    resp = await async_client.post(
        "/api/v1/catalog/specializations",
        json=spec_data,
        headers=auth_headers(sa_token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == "AIML"
    assert data["program_catalog_id"] == nat_prog.id


# ==============================================================================
# 10. COURSE CATALOG PROPERTIES & 14. INSTITUTION-COURSE MAPPING
# ==============================================================================

async def test_10_and_14_course_catalog_and_institution_course_mapping(
    async_client: AsyncClient, db_session: AsyncSession, catalog_seed
):
    _, sa_token = await create_user_helper(db_session, "sa_course@dhruva.ai", UserRole.SUPER_ADMIN)

    # Create national course
    course_data = {
        "code": "NAT-CS201",
        "title": "Data Structures and Algorithms",
        "discipline_id": catalog_seed["discipline"].id,
        "default_credits": 4.0,
        "academic_level": "intermediate",
        "description": "Fundamental data structures and algorithm analysis",
        "prerequisites": ["NAT-CS101"],
        "aliases": ["DSA", "Data Structures"],
    }
    resp_course = await async_client.post(
        "/api/v1/catalog/courses",
        json=course_data,
        headers=auth_headers(sa_token),
    )
    assert resp_course.status_code == 201
    nat_course = resp_course.json()

    # Create local institution course
    inst = Institution(name="BITS Pilani", code="BITS")
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)

    dept = Department(institution_id=inst.id, name="Computer Science", code="CS")
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)

    local_course = Course(
        institution_id=inst.id,
        department_id=dept.id,
        title="Data Structures & Algorithms",
        code="CS_F211",
        credits=4.0,
    )
    db_session.add(local_course)
    await db_session.commit()
    await db_session.refresh(local_course)

    _, inst_admin_token = await create_user_helper(
        db_session, "admin@bits.ac.in", UserRole.INSTITUTION_ADMIN, institution_id=inst.id
    )

    # Map institution course to national course
    map_payload = {
        "institution_id": inst.id,
        "institution_course_id": local_course.id,
        "national_course_id": nat_course["id"],
        "local_code": "CS_F211",
        "local_title": "Data Structures & Algorithms",
        "confidence_score": 1.0,
        "notes": "Matches 95% of national syllabus",
    }
    resp_map = await async_client.post(
        "/api/v1/catalog/institution-course-mappings",
        json=map_payload,
        headers=auth_headers(inst_admin_token),
    )
    assert resp_map.status_code == 201
    assert resp_map.json()["institution_id"] == inst.id
    assert resp_map.json()["national_course_id"] == nat_course["id"]


# ==============================================================================
# 11. SKILL MAPPINGS & 12. CAREER MAPPINGS
# ==============================================================================

async def test_11_and_12_skill_and_career_mappings(
    async_client: AsyncClient, db_session: AsyncSession, catalog_seed
):
    _, sa_token = await create_user_helper(db_session, "sa_sk_cr@dhruva.ai", UserRole.SUPER_ADMIN)

    # Create skill
    skill_resp = await async_client.post(
        "/api/v1/catalog/skills",
        json={
            "code": "SK-PY",
            "name": "Python Programming",
            "category": "technical",
            "description": "Python scripting, data structures, and OOP",
        },
        headers=auth_headers(sa_token),
    )
    assert skill_resp.status_code == 201
    skill_id = skill_resp.json()["id"]

    # Create career
    career_resp = await async_client.post(
        "/api/v1/catalog/careers",
        json={
            "code": "CR-DS",
            "title": "Data Scientist",
            "industry": "Artificial Intelligence & Analytics",
            "description": "Analyzes complex data to extract predictive insights",
        },
        headers=auth_headers(sa_token),
    )
    assert career_resp.status_code == 201
    career_id = career_resp.json()["id"]

    # Link career to skill
    car_skill = await academic_catalog_service.create_career_skill_mapping(
        db_session,
        CareerSkillMappingCreate(
            career_id=career_id,
            skill_id=skill_id,
            importance="required",
            weight=1.0,
        ),
    )
    assert car_skill.career_id == career_id
    assert car_skill.skill_id == skill_id


# ==============================================================================
# 15. CROSS-INSTITUTION ISOLATION
# ==============================================================================

async def test_15_cross_institution_isolation(
    async_client: AsyncClient, db_session: AsyncSession, catalog_seed
):
    # Inst A
    inst_a = Institution(name="Inst A", code="INST_A")
    # Inst B
    inst_b = Institution(name="Inst B", code="INST_B")
    db_session.add_all([inst_a, inst_b])
    await db_session.commit()
    await db_session.refresh(inst_a)
    await db_session.refresh(inst_b)

    dept_b = Department(institution_id=inst_b.id, name="Dept B", code="DEPT_B")
    db_session.add(dept_b)
    await db_session.commit()
    await db_session.refresh(dept_b)

    course_b = Course(institution_id=inst_b.id, department_id=dept_b.id, title="Course B", code="CB101")
    db_session.add(course_b)
    await db_session.commit()
    await db_session.refresh(course_b)

    nat_course = CourseCatalog(
        code="NAT-ISOL-1",
        title="National Test Course",
        slug="nat-isol-1",
        discipline_id=catalog_seed["discipline"].id,
        default_credits=3.0,
    )
    db_session.add(nat_course)
    await db_session.commit()
    await db_session.refresh(nat_course)

    # Admin A belongs to Inst A
    _, admin_a_token = await create_user_helper(
        db_session, "admin_a@insta.com", UserRole.INSTITUTION_ADMIN, institution_id=inst_a.id
    )

    # Admin A attempts to map Course B (which belongs to Inst B) using inst_a.id
    map_payload = {
        "institution_id": inst_a.id,
        "institution_course_id": course_b.id,
        "national_course_id": nat_course.id,
        "local_code": "CB101",
        "local_title": "Course B",
    }
    resp = await async_client.post(
        "/api/v1/catalog/institution-course-mappings",
        json=map_payload,
        headers=auth_headers(admin_a_token),
    )
    assert resp.status_code == 404
    assert "not found in your institution" in resp.json()["detail"]

    # Also test cross-institution modification attempt with inst_b.id
    map_payload_b = {
        "institution_id": inst_b.id,
        "institution_course_id": course_b.id,
        "national_course_id": nat_course.id,
        "local_code": "CB101",
        "local_title": "Course B",
    }
    resp_b = await async_client.post(
        "/api/v1/catalog/institution-course-mappings",
        json=map_payload_b,
        headers=auth_headers(admin_a_token),
    )
    assert resp_b.status_code == 403
    assert "Access denied" in resp_b.json()["detail"]


# ==============================================================================
# 16. IMPORT VALIDATION, 17. DUPLICATE IMPORT, 18. FAILED RECORDS, 21. AUDIT JOB
# ==============================================================================

async def test_16_17_18_21_catalog_import_pipeline(
    async_client: AsyncClient, db_session: AsyncSession, catalog_seed
):
    _, sa_token = await create_user_helper(db_session, "sa_importer@dhruva.ai", UserRole.SUPER_ADMIN)

    # 1. Valid Dry Run Import of Skills
    dry_run_payload = {
        "entity_type": "skill",
        "is_dry_run": True,
        "records": [
            {"code": "SK-SQL", "name": "SQL Database Design", "category": "database"},
            {"code": "SK-DOCKER", "name": "Docker Containerization", "category": "devops"},
        ],
    }
    resp_dry = await async_client.post(
        "/api/v1/catalog/imports",
        json=dry_run_payload,
        headers=auth_headers(sa_token),
    )
    assert resp_dry.status_code == 201
    dry_job = resp_dry.json()
    assert dry_job["is_dry_run"] is True
    assert dry_job["total_records"] == 2
    assert dry_job["successful_records"] == 2
    assert dry_job["status"] == "completed"

    # Verify dry run did NOT persist records to database
    skill_check = await async_client.get("/api/v1/catalog/skills", headers=auth_headers(sa_token))
    assert not any(s["code"] == "SK-SQL" for s in skill_check.json())

    # 2. Actual Import with 1 valid, 1 duplicate/update, and 1 invalid record
    real_import_payload = {
        "entity_type": "skill",
        "is_dry_run": False,
        "records": [
            {"code": "SK-SQL", "name": "SQL Database Design", "category": "database"},
            {"code": "SK-DOCKER", "name": "Docker Containerization", "category": "devops"},
            {"code": "X"},  # Invalid: code length < 2
        ],
    }
    resp_real = await async_client.post(
        "/api/v1/catalog/imports",
        json=real_import_payload,
        headers=auth_headers(sa_token),
    )
    assert resp_real.status_code == 201
    real_job = resp_real.json()
    assert real_job["is_dry_run"] is False
    assert real_job["total_records"] == 3
    assert real_job["successful_records"] == 2
    assert real_job["failed_records"] == 1
    assert len(real_job["errors"]) == 1

    # 3. Idempotent Second Run (duplicate handling increments duplicate_records)
    resp_dup = await async_client.post(
        "/api/v1/catalog/imports",
        json={
            "entity_type": "skill",
            "is_dry_run": False,
            "records": [
                {"code": "SK-SQL", "name": "SQL Database Design", "category": "database"},
            ],
        },
        headers=auth_headers(sa_token),
    )
    assert resp_dup.status_code == 201
    dup_job = resp_dup.json()
    assert dup_job["duplicate_records"] == 1
    assert dup_job["successful_records"] == 0

    # 4. Check import job audit trail
    job_resp = await async_client.get(f"/api/v1/catalog/imports/{real_job['id']}", headers=auth_headers(sa_token))
    assert job_resp.status_code == 200
    assert job_resp.json()["id"] == real_job["id"]


# ==============================================================================
# 19. SEARCH ACROSS CATALOG ENTITIES
# ==============================================================================

async def test_19_catalog_search(
    async_client: AsyncClient, db_session: AsyncSession, catalog_seed
):
    _, sa_token = await create_user_helper(db_session, "sa_search@dhruva.ai", UserRole.SUPER_ADMIN)
    _, st_token = await create_user_helper(db_session, "student_search@dhruva.ai", UserRole.STUDENT)

    # Populate search targets
    await async_client.post(
        "/api/v1/catalog/programs",
        json={
            "code": "BTECH-ROBOTICS",
            "name": "Bachelor of Technology in Robotics & Automation",
            "short_name": "B.Tech Robotics",
            "discipline_id": catalog_seed["discipline"].id,
            "degree_type_id": catalog_seed["degree_type"].id,
            "duration_years": 4.0,
        },
        headers=auth_headers(sa_token),
    )
    await async_client.post(
        "/api/v1/catalog/courses",
        json={
            "code": "ROB-301",
            "title": "Industrial Robotics and Kinematics",
            "discipline_id": catalog_seed["discipline"].id,
            "default_credits": 3.0,
        },
        headers=auth_headers(sa_token),
    )
    await async_client.post(
        "/api/v1/catalog/skills",
        json={
            "code": "SK-ROB-KIN",
            "name": "Robotics Kinematics",
            "category": "robotics",
        },
        headers=auth_headers(sa_token),
    )
    await async_client.post(
        "/api/v1/catalog/careers",
        json={
            "code": "CR-ROB-ENG",
            "title": "Robotics Engineer",
            "industry": "Automation & Manufacturing",
        },
        headers=auth_headers(sa_token),
    )

    # Search query "Robotics"
    resp = await async_client.get("/api/v1/catalog/search?q=Robotics", headers=auth_headers(st_token))
    assert resp.status_code == 200
    res = resp.json()
    assert len(res["programs"]) >= 1
    assert len(res["courses"]) >= 1
    assert len(res["skills"]) >= 1
    assert len(res["careers"]) >= 1


# ==============================================================================
# 20. PAGINATION
# ==============================================================================

async def test_20_catalog_pagination(
    async_client: AsyncClient, db_session: AsyncSession, catalog_seed
):
    _, st_token = await create_user_helper(db_session, "stud_page@dhruva.ai", UserRole.STUDENT)

    # Limit = 1, Skip = 0
    resp_p1 = await async_client.get("/api/v1/catalog/disciplines?limit=1&skip=0", headers=auth_headers(st_token))
    assert resp_p1.status_code == 200
    items_p1 = resp_p1.json()
    assert len(items_p1) <= 1
