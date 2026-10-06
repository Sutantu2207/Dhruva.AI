"""DHRUVA.AI - Seed Script: Isolated Synthetic Pilot Institution & 50+ Student Cohort.

Idempotently provisions:
- "Dhruva Demo University" (DHRUVA-DEMO-U)
- 5 Engineering Departments (CSE, IT, ECE, MECH, CIVIL)
- Academic Hierarchy (Programs, Batches, Sections, Academic Years, Semesters)
- Institutional Course Offerings & Teaching Assignments
- Synthetic Faculty Accounts across Departments
- 50 Synthetic Students with diverse, deterministic learning histories across 6 cohorts:
  1. High Mastery Achievers (Mastery >0.85, Verified Projects, High Portfolio Health)
  2. Consistent Average Learners (Mastery 0.60-0.75, Steady Progress)
  3. Prerequisite Gaps & Active Remediation (Triggers Domain 10 Remediation Plans & Diagnoses)
  4. Retention Decay / SM-2 Overdue (Review Due >30 Days ago, Retention <0.60)
  5. Strong Practical Code / Weak Theory
  6. At-Risk Learners (Triggers Domain 9 Early Intervention Signals)
"""

import asyncio
import logging
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.core.security import UserRole, get_password_hash
from app.scripts import ensure_seed_safety
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
    TeacherAcademicProfile,
    TeachingAssignment,
    StudentAcademicProfile,
    StudentEnrollment,
)
from app.domains.catalog.models import CareerCatalog, SkillCatalog
from app.domains.content.models import Concept
from app.domains.assessment.models import (
    Assessment,
    AssessmentVersion,
    AssessmentAttempt,
    ConceptEvidence,
)
from app.domains.mastery.models import (
    StudentConceptKnowledgeState,
    ConceptReviewState,
)
from app.domains.profiles.models import (
    StudentProject,
    StudentCareerGoal,
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

logger = logging.getLogger("dhruva.seed_demo_institution")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


DEPARTMENTS_CONFIG = [
    {"code": "DHR-CSE", "name": "Department of Computer Science & Engineering"},
    {"code": "DHR-IT", "name": "Department of Information Technology"},
    {"code": "DHR-ECE", "name": "Department of Electronics & Communication Engineering"},
    {"code": "DHR-MECH", "name": "Department of Mechanical Engineering"},
    {"code": "DHR-CIVIL", "name": "Department of Civil Engineering"},
]

FACULTY_CONFIG = [
    {
        "email": "faculty.cse01@example.invalid",
        "first_name": "Aarav",
        "last_name": "Sharma",
        "role": UserRole.HOD,
        "dept_code": "DHR-CSE",
        "designation": "Professor & HOD",
        "employee_id": "FAC-CSE-001",
    },
    {
        "email": "faculty.cse02@example.invalid",
        "first_name": "Priya",
        "last_name": "Nair",
        "role": UserRole.TEACHER,
        "dept_code": "DHR-CSE",
        "designation": "Assistant Professor",
        "employee_id": "FAC-CSE-002",
    },
    {
        "email": "faculty.it01@example.invalid",
        "first_name": "Rohan",
        "last_name": "Desai",
        "role": UserRole.HOD,
        "dept_code": "DHR-IT",
        "designation": "Associate Professor & HOD",
        "employee_id": "FAC-IT-001",
    },
    {
        "email": "faculty.ece01@example.invalid",
        "first_name": "Vikram",
        "last_name": "Rao",
        "role": UserRole.TEACHER,
        "dept_code": "DHR-ECE",
        "designation": "Associate Professor",
        "employee_id": "FAC-ECE-001",
    },
    {
        "email": "faculty.mech01@example.invalid",
        "first_name": "Neha",
        "last_name": "Gupta",
        "role": UserRole.TEACHER,
        "dept_code": "DHR-MECH",
        "designation": "Assistant Professor",
        "employee_id": "FAC-MECH-001",
    },
]

COURSES_CONFIG = [
    {"code": "CSE101", "title": "Python Programming Fundamentals", "dept_code": "DHR-CSE", "credits": 3.0},
    {"code": "CSE201", "title": "Data Structures & Algorithms", "dept_code": "DHR-CSE", "credits": 4.0},
    {"code": "CSE301", "title": "Database Management Systems", "dept_code": "DHR-CSE", "credits": 3.0},
    {"code": "CSE401", "title": "Full Stack Web Application Development", "dept_code": "DHR-CSE", "credits": 4.0},
]


async def seed_demo_institution_and_cohort(db: AsyncSession) -> Dict[str, int]:
    """Provisions Dhruva Demo University with full academic hierarchy and 50 diverse student histories."""
    ensure_seed_safety(allow_synthetic=True)

    stats = {
        "institutions": 0,
        "departments": 0,
        "programs": 0,
        "batches": 0,
        "sections": 0,
        "faculty": 0,
        "courses": 0,
        "offerings": 0,
        "students": 0,
        "enrollments": 0,
        "knowledge_states": 0,
        "review_states": 0,
        "projects": 0,
        "project_evidences": 0,
        "project_reviews": 0,
        "portfolio_snapshots": 0,
        "intervention_signals": 0,
        "remediation_plans": 0,
    }

    # 1. Pilot Institution
    inst_res = await db.execute(select(Institution).where(Institution.code == "DHRUVA-DEMO-U"))
    inst = inst_res.scalar_one_or_none()
    if not inst:
        inst = Institution(
            code="DHRUVA-DEMO-U",
            name="Dhruva Demo University (Synthetic Pilot)",
            email_domains="example.invalid,demo.invalid",
            status="active",
        )
        db.add(inst)
        await db.flush()
        stats["institutions"] += 1

    # 2. Academic Departments
    dept_map: Dict[str, Department] = {}
    for d_data in DEPARTMENTS_CONFIG:
        res = await db.execute(
            select(Department).where(
                Department.institution_id == inst.id,
                Department.code == d_data["code"],
            )
        )
        dept = res.scalar_one_or_none()
        if not dept:
            dept = Department(
                institution_id=inst.id,
                code=d_data["code"],
                name=d_data["name"],
                status="active",
            )
            db.add(dept)
            await db.flush()
            stats["departments"] += 1
        dept_map[d_data["code"]] = dept

    # 3. Degree Programs
    cse_dept = dept_map["DHR-CSE"]
    prog_res = await db.execute(
        select(Program).where(Program.department_id == cse_dept.id, Program.code == "BE-CSE")
    )
    cse_prog = prog_res.scalar_one_or_none()
    if not cse_prog:
        cse_prog = Program(
            department_id=cse_dept.id,
            code="BE-CSE",
            name="B.Tech Computer Science & Engineering",
            degree_type="B.Tech",
            duration_years=4,
            status="active",
        )
        db.add(cse_prog)
        await db.flush()
        stats["programs"] += 1

    # 4. Academic Year & Semesters
    ay_res = await db.execute(
        select(AcademicYear).where(AcademicYear.institution_id == inst.id, AcademicYear.name == "2026-27")
    )
    ay = ay_res.scalar_one_or_none()
    if not ay:
        ay = AcademicYear(
            institution_id=inst.id,
            name="2026-27",
            start_date=date(2026, 7, 1),
            end_date=date(2027, 6, 30),
            status="active",
        )
        db.add(ay)
        await db.flush()

    sem_res = await db.execute(
        select(Semester).where(Semester.academic_year_id == ay.id, Semester.semester_number == 5)
    )
    sem5 = sem_res.scalar_one_or_none()
    if not sem5:
        sem5 = Semester(
            academic_year_id=ay.id,
            semester_number=5,
            label="Semester 5 (Odd 2026)",
            start_date=date(2026, 7, 15),
            end_date=date(2026, 12, 15),
            status="active",
        )
        db.add(sem5)
        await db.flush()

    # 5. Batches & Sections
    batch_res = await db.execute(
        select(Batch).where(Batch.program_id == cse_prog.id, Batch.label == "2024-2028")
    )
    batch = batch_res.scalar_one_or_none()
    if not batch:
        batch = Batch(
            institution_id=inst.id,
            program_id=cse_prog.id,
            admission_year=2024,
            graduation_year=2028,
            label="2024-2028",
            status="active",
        )
        db.add(batch)
        await db.flush()
        stats["batches"] += 1

    sec_res = await db.execute(
        select(Section).where(Section.batch_id == batch.id, Section.name == "A")
    )
    sec_a = sec_res.scalar_one_or_none()
    if not sec_a:
        sec_a = Section(batch_id=batch.id, name="A", capacity=60, status="active")
        db.add(sec_a)
        await db.flush()
        stats["sections"] += 1

    sec_b_res = await db.execute(
        select(Section).where(Section.batch_id == batch.id, Section.name == "B")
    )
    sec_b = sec_b_res.scalar_one_or_none()
    if not sec_b:
        sec_b = Section(batch_id=batch.id, name="B", capacity=60, status="active")
        db.add(sec_b)
        await db.flush()
        stats["sections"] += 1

    # 6. Faculty Accounts & Profiles
    faculty_profiles: List[TeacherAcademicProfile] = []
    default_pw_hash = get_password_hash("DhruvaPilotFaculty2026!")

    for f_data in FACULTY_CONFIG:
        u_res = await db.execute(select(User).where(User.email == f_data["email"]))
        user = u_res.scalar_one_or_none()
        if not user:
            user = User(
                email=f_data["email"],
                normalized_email=f_data["email"].lower(),
                hashed_password=default_pw_hash,
                role=f_data["role"],
                first_name=f_data["first_name"],
                last_name=f_data["last_name"],
                display_name=f"{f_data['first_name']} {f_data['last_name']} (Pilot)",
                institution_id=inst.id,
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            await db.flush()
            stats["faculty"] += 1

        dept = dept_map[f_data["dept_code"]]
        fp_res = await db.execute(
            select(TeacherAcademicProfile).where(TeacherAcademicProfile.user_id == user.id)
        )
        fp = fp_res.scalar_one_or_none()
        if not fp:
            fp = TeacherAcademicProfile(
                user_id=user.id,
                institution_id=inst.id,
                department_id=dept.id,
                designation=f_data["designation"],
                employee_id=f_data["employee_id"],
                status="active",
            )
            db.add(fp)
            await db.flush()
        faculty_profiles.append(fp)

    lead_faculty = faculty_profiles[0]  # Dr. Aarav Sharma

    # 7. Courses & Offerings
    offerings_map: Dict[str, CourseOffering] = {}
    for c_data in COURSES_CONFIG:
        dept = dept_map[c_data["dept_code"]]
        c_res = await db.execute(
            select(Course).where(Course.institution_id == inst.id, Course.code == c_data["code"])
        )
        course = c_res.scalar_one_or_none()
        if not course:
            course = Course(
                institution_id=inst.id,
                department_id=dept.id,
                code=c_data["code"],
                title=c_data["title"],
                credits=c_data["credits"],
                status="active",
            )
            db.add(course)
            await db.flush()
            stats["courses"] += 1

        off_res = await db.execute(
            select(CourseOffering).where(
                CourseOffering.course_id == course.id,
                CourseOffering.academic_year_id == ay.id,
                CourseOffering.semester_id == sem5.id,
                CourseOffering.section_id == sec_a.id,
            )
        )
        offering = off_res.scalar_one_or_none()
        if not offering:
            offering = CourseOffering(
                course_id=course.id,
                academic_year_id=ay.id,
                semester_id=sem5.id,
                section_id=sec_a.id,
                status="active",
            )
            db.add(offering)
            await db.flush()
            stats["offerings"] += 1

            # Assign Lead Faculty
            ta = TeachingAssignment(
                teacher_profile_id=lead_faculty.id,
                course_offering_id=offering.id,
                assignment_role="lead_instructor",
                status="active",
            )
            db.add(ta)

        offerings_map[c_data["code"]] = offering

    # Pre-fetch canonical concepts & skills for evidence assignment
    concept_res = await db.execute(select(Concept))
    concepts = {c.name: c for c in concept_res.scalars().all()}

    career_res = await db.execute(select(CareerCatalog))
    careers = {c.code: c for c in career_res.scalars().all()}
    swe_career = careers.get("CAR-SWE")
    fs_career = careers.get("CAR-FULLSTACK")

    py_concept = concepts.get("Python Variables and Primitive Types")
    func_concept = concepts.get("Python Functions and Scoping")
    dsa_concept = concepts.get("Binary Trees and Tree Traversals")
    dbms_concept = concepts.get("SQL Joins and Multi-Table Queries")

    student_pw_hash = get_password_hash("PilotStudentPassword2026!")

    # 8. Seed 50 Diverse Students Across 6 Analytical Cohorts
    for i in range(1, 51):
        padded_num = f"{i:02d}"
        email = f"student.cse{padded_num}@example.invalid"
        enrollment_no = f"DHR2024CSE{padded_num}"
        assigned_section = sec_a if i <= 25 else sec_b

        u_res = await db.execute(select(User).where(User.email == email))
        user = u_res.scalar_one_or_none()
        if not user:
            user = User(
                email=email,
                normalized_email=email.lower(),
                hashed_password=student_pw_hash,
                role=UserRole.STUDENT,
                first_name=f"PilotStudent",
                last_name=padded_num,
                display_name=f"Pilot Student {padded_num}",
                institution_id=inst.id,
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            await db.flush()
            stats["students"] += 1

        sp_res = await db.execute(
            select(StudentAcademicProfile).where(StudentAcademicProfile.user_id == user.id)
        )
        sp = sp_res.scalar_one_or_none()
        if not sp:
            sp = StudentAcademicProfile(
                user_id=user.id,
                institution_id=inst.id,
                program_id=cse_prog.id,
                batch_id=batch.id,
                current_section_id=assigned_section.id,
                enrollment_number=enrollment_no,
                admission_year=2024,
                graduation_year=2028,
                academic_status="active",
            )
            db.add(sp)
            await db.flush()

        # Enroll in Offerings
        for off in offerings_map.values():
            enr_res = await db.execute(
                select(StudentEnrollment).where(
                    StudentEnrollment.student_profile_id == sp.id,
                    StudentEnrollment.course_offering_id == off.id,
                )
            )
            if not enr_res.scalar_one_or_none():
                enr = StudentEnrollment(
                    student_profile_id=sp.id,
                    course_offering_id=off.id,
                    enrollment_status="enrolled",
                )
                db.add(enr)
                stats["enrollments"] += 1

        # Career Goal
        if swe_career:
            cg_res = await db.execute(
                select(StudentCareerGoal).where(
                    StudentCareerGoal.student_profile_id == sp.id,
                    StudentCareerGoal.career_catalog_id == swe_career.id,
                )
            )
            if not cg_res.scalar_one_or_none():
                cg = StudentCareerGoal(
                    student_profile_id=sp.id,
                    career_catalog_id=swe_career.id,
                    priority=1,
                    short_term_goals="Targeting core software engineering role with emphasis on algorithmic efficiency.",
                )
                db.add(cg)

        # -------------------------------------------------------------
        # SYNTHETIC EVIDENCE AND DETERMINISTIC HISTORIES BY COHORT
        # -------------------------------------------------------------

        # Cohort 1: High Mastery Achievers (Students 1 to 10)
        if 1 <= i <= 10:
            if dsa_concept:
                ks_chk = await db.execute(
                    select(StudentConceptKnowledgeState).where(
                        StudentConceptKnowledgeState.student_profile_id == sp.id,
                        StudentConceptKnowledgeState.concept_id == dsa_concept.id,
                    )
                )
                if not ks_chk.scalar_one_or_none():
                    ks = StudentConceptKnowledgeState(
                        student_profile_id=sp.id,
                        concept_id=dsa_concept.id,
                        current_mastery=Decimal("0.9200"),
                        confidence=Decimal("0.8500"),
                        retention_estimate=Decimal("0.9500"),
                        state="mastered",
                        trend="improving",
                        evidence_count=6,
                    )
                    db.add(ks)
                    stats["knowledge_states"] += 1

            # High Quality Verified Project
            pj_chk = await db.execute(
                select(StudentProject).where(
                    StudentProject.student_profile_id == sp.id,
                    StudentProject.title == "Distributed In-Memory Key-Value Store",
                )
            )
            if not pj_chk.scalar_one_or_none():
                proj = StudentProject(
                    student_profile_id=sp.id,
                    title="Distributed In-Memory Key-Value Store",
                    project_type="capstone",
                    status="completed",
                    is_verified=True,
                    verification_status="verified",
                    quality_score=92.5,
                    career_relevance_score=95.0,
                    technologies=["Python", "Sockets", "Concurrency", "Algorithms"],
                    repository_url=f"https://github.com/pilot-student-{padded_num}/distributed-kv-store",
                )
                db.add(proj)
                await db.flush()
                stats["projects"] += 1

                pe = ProjectEvidence(
                    project_id=proj.id,
                    student_profile_id=sp.id,
                    evidence_type="repository",
                    source="github",
                    source_reference=f"https://github.com/pilot-student-{padded_num}/distributed-kv-store",
                    title="Git Repository & Automated CI Tests",
                    verification_status="verified",
                    evidence_strength=0.95,
                )
                db.add(pe)
                stats["project_evidences"] += 1

                rev = ProjectReview(
                    project_id=proj.id,
                    reviewer_user_id=lead_faculty.user_id,
                    review_type="faculty",
                    technical_depth=94.0,
                    problem_solving=92.0,
                    code_quality=90.0,
                    architecture_quality=92.0,
                    documentation_quality=90.0,
                    testing_quality=90.0,
                    practical_application=92.0,
                    originality=88.0,
                    student_contribution_score=95.0,
                    professional_presentation=92.0,
                    overall_score=91.7,
                    decision="approved",
                    feedback="Exemplary engineering rigor and comprehensive test suite coverage.",
                )
                db.add(rev)
                stats["project_reviews"] += 1

                snap = PortfolioIntelligenceSnapshot(
                    student_profile_id=sp.id,
                    overall_health_score=92.0,
                    status="assessed",
                    technical_depth=92.0,
                    evidence_quality=95.0,
                    career_alignment=94.0,
                    completeness_score=90.0,
                )
                db.add(snap)
                stats["portfolio_snapshots"] += 1

        # Cohort 2: Average Consistent Learners (Students 11 to 25)
        elif 11 <= i <= 25:
            if py_concept:
                ks_chk = await db.execute(
                    select(StudentConceptKnowledgeState).where(
                        StudentConceptKnowledgeState.student_profile_id == sp.id,
                        StudentConceptKnowledgeState.concept_id == py_concept.id,
                    )
                )
                if not ks_chk.scalar_one_or_none():
                    ks = StudentConceptKnowledgeState(
                        student_profile_id=sp.id,
                        concept_id=py_concept.id,
                        current_mastery=Decimal("0.7200"),
                        confidence=Decimal("0.7000"),
                        retention_estimate=Decimal("0.8000"),
                        state="developing",
                        trend="stable",
                        evidence_count=3,
                    )
                    db.add(ks)
                    stats["knowledge_states"] += 1

        # Cohort 3: Prerequisite Gap & Active Remediation (Students 26 to 35)
        elif 26 <= i <= 35:
            if dsa_concept:
                ks_chk = await db.execute(
                    select(StudentConceptKnowledgeState).where(
                        StudentConceptKnowledgeState.student_profile_id == sp.id,
                        StudentConceptKnowledgeState.concept_id == dsa_concept.id,
                    )
                )
                if not ks_chk.scalar_one_or_none():
                    ks = StudentConceptKnowledgeState(
                        student_profile_id=sp.id,
                        concept_id=dsa_concept.id,
                        current_mastery=Decimal("0.3500"),
                        confidence=Decimal("0.6500"),
                        retention_estimate=Decimal("0.7000"),
                        state="at_risk",
                        trend="declining",
                        prerequisite_health="weak",
                        prerequisite_readiness=Decimal("0.3000"),
                        evidence_count=4,
                    )
                    db.add(ks)
                    stats["knowledge_states"] += 1

                # Active Deterministic Remediation Plan
                rem_key = f"rem-pilot-{sp.id}-{dsa_concept.id}"
                rp_chk = await db.execute(
                    select(RemediationPlan).where(RemediationPlan.idempotency_key == rem_key)
                )
                if not rp_chk.scalar_one_or_none():
                    rp = RemediationPlan(
                        student_profile_id=sp.id,
                        target_concept_id=dsa_concept.id,
                        diagnosis_type="PREREQUISITE_GAP",
                        diagnosis_reason="Diagnostic evaluation detected deficiency in prerequisite concept: Python Functions and Control Flow.",
                        priority_score=Decimal("0.7800"),
                        status="in_progress",
                        idempotency_key=rem_key,
                    )
                    db.add(rp)
                    await db.flush()
                    stats["remediation_plans"] += 1

                    diag = RemediationDiagnosis(
                        remediation_plan_id=rp.id,
                        concept_id=dsa_concept.id,
                        evidence_count=4,
                        mastery_before=Decimal("0.3500"),
                        confidence_before=Decimal("0.6500"),
                        retention_before=Decimal("0.7000"),
                        diagnosis_category="PREREQUISITE_GAP",
                        diagnosis_reason="Diagnostic evaluation detected deficiency in prerequisite concept: Python Functions and Control Flow.",
                        explanation_payload={"deficiency": "Python Functions and Control Flow"},
                    )
                    db.add(diag)

                    step1 = RemediationPlanStep(
                        remediation_plan_id=rp.id,
                        sequence_order=1,
                        step_type="PREREQUISITE",
                        concept_id=func_concept.id if func_concept else dsa_concept.id,
                        title="Review Prerequisite: Python Functions & Recursion Basics",
                        completion_status="completed",
                        required=True,
                    )
                    db.add(step1)

                    step2 = RemediationPlanStep(
                        remediation_plan_id=rp.id,
                        sequence_order=2,
                        step_type="GUIDED_PRACTICE",
                        concept_id=dsa_concept.id,
                        title="Interactive Guided Practice: Binary Tree Pointer Traversals",
                        completion_status="in_progress",
                        required=True,
                    )
                    db.add(step2)

        # Cohort 4: Retention Decay / SM-2 Due (Students 36 to 42)
        elif 36 <= i <= 42:
            if dbms_concept:
                past_date = datetime.now(timezone.utc) - timedelta(days=35)
                ks_chk = await db.execute(
                    select(StudentConceptKnowledgeState).where(
                        StudentConceptKnowledgeState.student_profile_id == sp.id,
                        StudentConceptKnowledgeState.concept_id == dbms_concept.id,
                    )
                )
                if not ks_chk.scalar_one_or_none():
                    ks = StudentConceptKnowledgeState(
                        student_profile_id=sp.id,
                        concept_id=dbms_concept.id,
                        current_mastery=Decimal("0.8500"),
                        confidence=Decimal("0.8000"),
                        retention_estimate=Decimal("0.5400"),  # Ebbinghaus decay over 35 days
                        state="proficient",
                        trend="declining",
                        evidence_count=5,
                        last_evidence_at=past_date,
                    )
                    db.add(ks)
                    stats["knowledge_states"] += 1

                crs_chk = await db.execute(
                    select(ConceptReviewState).where(
                        ConceptReviewState.student_profile_id == sp.id,
                        ConceptReviewState.concept_id == dbms_concept.id,
                    )
                )
                if not crs_chk.scalar_one_or_none():
                    crs = ConceptReviewState(
                        student_profile_id=sp.id,
                        concept_id=dbms_concept.id,
                        interval_days=14,
                        ease_factor=Decimal("2.4000"),
                        repetition=3,
                        last_reviewed_at=past_date,
                        next_review_at=past_date + timedelta(days=14),
                        review_status="overdue",
                    )
                    db.add(crs)
                    stats["review_states"] += 1

        # Cohort 5: Strong Practical / Weak Theory (Students 43 to 46)
        elif 43 <= i <= 46:
            pj_chk = await db.execute(
                select(StudentProject).where(
                    StudentProject.student_profile_id == sp.id,
                    StudentProject.title == "Full Stack Micro-Blogging Application",
                )
            )
            if not pj_chk.scalar_one_or_none():
                proj = StudentProject(
                    student_profile_id=sp.id,
                    title="Full Stack Micro-Blogging Application",
                    project_type="personal",
                    status="completed",
                    is_verified=True,
                    verification_status="verified",
                    quality_score=78.0,
                    career_relevance_score=85.0,
                    technologies=["React", "Node.js", "Express", "PostgreSQL"],
                    repository_url=f"https://github.com/pilot-student-{padded_num}/microblog",
                )
                db.add(proj)
                await db.flush()
                stats["projects"] += 1

                pe = ProjectEvidence(
                    project_id=proj.id,
                    student_profile_id=sp.id,
                    evidence_type="repository",
                    source="github",
                    source_reference=f"https://github.com/pilot-student-{padded_num}/microblog",
                    title="Application Codebase",
                    verification_status="verified",
                    evidence_strength=0.88,
                )
                db.add(pe)
                stats["project_evidences"] += 1

        # Cohort 6: At-Risk Learners / Intervention Signals (Students 47 to 50)
        else:
            if py_concept:
                ks_chk = await db.execute(
                    select(StudentConceptKnowledgeState).where(
                        StudentConceptKnowledgeState.student_profile_id == sp.id,
                        StudentConceptKnowledgeState.concept_id == py_concept.id,
                    )
                )
                if not ks_chk.scalar_one_or_none():
                    ks = StudentConceptKnowledgeState(
                        student_profile_id=sp.id,
                        concept_id=py_concept.id,
                        current_mastery=Decimal("0.2800"),
                        confidence=Decimal("0.4000"),
                        retention_estimate=Decimal("0.6000"),
                        state="at_risk",
                        trend="strongly_declining",
                        evidence_count=2,
                    )
                    db.add(ks)
                    stats["knowledge_states"] += 1

            sig_chk = await db.execute(
                select(AcademicInterventionSignal).where(
                    AcademicInterventionSignal.student_profile_id == sp.id,
                    AcademicInterventionSignal.signal_type == "repeated_assessment_failures",
                )
            )
            if not sig_chk.scalar_one_or_none():
                signal = AcademicInterventionSignal(
                    institution_id=inst.id,
                    student_profile_id=sp.id,
                    course_offering_id=offerings_map["CSE101"].id,
                    signal_type="repeated_assessment_failures",
                    severity="high",
                    title=f"Consecutive Assessment Deficiency: Student {padded_num}",
                    evidence_data={
                        "consecutive_failures": 2,
                        "average_score": 32.5,
                        "affected_concept": "Python Variables and Control Flow",
                    },
                    recommended_action="Faculty diagnostic meeting and mandatory prerequisite refresher assignment.",
                    status="detected",
                )
                db.add(signal)
                stats["intervention_signals"] += 1

    await db.commit()
    logger.info("Dhruva Demo University & 50 Synthetic Students seeded successfully: %s", stats)
    return stats


async def main():
    async with async_session_maker() as db:
        await seed_demo_institution_and_cohort(db)


if __name__ == "__main__":
    asyncio.run(main())
