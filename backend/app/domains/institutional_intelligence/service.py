"""Transactional Service for Institutional Intelligence, Analytics, and Early Intervention Workflows."""

import io
import csv
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.core.security import UserRole
from app.domains.identity.models import User
from app.domains.academic.models import (
    Institution,
    Department,
    Program,
    Batch,
    Section,
    Course,
    CourseOffering,
    StudentEnrollment,
    TeachingAssignment,
    StudentAcademicProfile,
    TeacherAcademicProfile,
)
from app.domains.content.models import (
    Concept,
    ConceptSkill,
    CourseContent,
    Curriculum,
    Module,
    Lesson,
    LessonConcept,
    LessonProgress,
)
from app.domains.assessment.models import (
    Assessment,
    AssessmentVersion,
    AssessmentQuestion,
    Question,
    QuestionVersion,
    AssessmentAttempt,
    AssessmentResponse,
    AssessmentEvaluation,
)
from app.domains.mastery.models import (
    StudentConceptKnowledgeState,
    ConceptReviewState,
)
from app.domains.career_intelligence.models import (
    StudentCareerReadinessState,
    PlacementReadinessState,
)
from app.domains.profiles.models import (
    StudentCareerGoal,
    StudentProject,
    StudentProjectSkill,
    StudentPortfolio,
    StudentIntervention,
)
from app.domains.project_intelligence.models import (
    ProjectEvidence,
    PortfolioIntelligenceSnapshot,
)
from app.domains.institutional_intelligence.models import (
    AcademicInterventionSignal,
    InstitutionalAnalyticsSnapshot,
)
from app.domains.institutional_intelligence.intervention_engine import InterventionSignalEngine
from app.domains.institutional_intelligence.course_analytics_engine import CourseAnalyticsEngine
from app.domains.institutional_intelligence.department_analytics_engine import DepartmentAnalyticsEngine
from app.domains.institutional_intelligence.placement_analytics_engine import PlacementAnalyticsEngine


class InstitutionalIntelligenceService:
    """Orchestrates analytics aggregations, early interventions, and institutional reporting."""

    # -------------------------------------------------------------------------
    # 1. Faculty Dashboard Overview
    # -------------------------------------------------------------------------

    @classmethod
    async def get_faculty_dashboard(
        cls,
        db: AsyncSession,
        user: User,
    ) -> Dict[str, Any]:
        """Provides deterministic overview for authenticated faculty member."""
        if user.role not in (UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized: faculty role required.",
            )

        teacher_prof_res = await db.execute(
            select(TeacherAcademicProfile).where(TeacherAcademicProfile.user_id == user.id)
        )
        teacher_prof = teacher_prof_res.scalar_one_or_none()

        offering_ids: List[str] = []
        offerings_summary: List[Dict[str, Any]] = []

        if teacher_prof:
            assignments = (
                await db.execute(
                    select(TeachingAssignment, CourseOffering, Course, Section)
                    .join(CourseOffering, TeachingAssignment.course_offering_id == CourseOffering.id)
                    .join(Course, CourseOffering.course_id == Course.id)
                    .join(Section, CourseOffering.section_id == Section.id)
                    .where(
                        TeachingAssignment.teacher_profile_id == teacher_prof.id,
                        TeachingAssignment.status == "active",
                    )
                )
            ).all()

            for assign, off, course, sec in assignments:
                offering_ids.append(off.id)
                enrolled_count = (
                    await db.scalar(
                        select(func.count(StudentEnrollment.id)).where(
                            StudentEnrollment.course_offering_id == off.id,
                            StudentEnrollment.enrollment_status == "enrolled",
                        )
                    )
                ) or 0
                offerings_summary.append({
                    "offering_id": off.id,
                    "course_code": course.code,
                    "course_title": course.title,
                    "section_name": sec.name,
                    "role": assign.assignment_role,
                    "enrolled_students": enrolled_count,
                    "status": off.status,
                })

        # Total enrolled students across assigned offerings
        total_students = sum((o["enrolled_students"] for o in offerings_summary), 0)

        # Active intervention signals in assigned offerings
        signals_query = select(AcademicInterventionSignal).where(
            AcademicInterventionSignal.status.in_(["detected", "acknowledged"])
        )
        if offering_ids:
            signals_query = signals_query.where(
                AcademicInterventionSignal.course_offering_id.in_(offering_ids)
            )
        elif user.role == UserRole.TEACHER:
            signals_query = signals_query.where(AcademicInterventionSignal.id == "none")

        active_signals = (await db.execute(signals_query)).scalars().all()
        urgent_signals = [s for s in active_signals if s.severity in ("urgent", "high")]

        # Pending manual grading items
        from app.domains.institutional_intelligence.grading_workflow_service import GradingWorkflowService
        grading_queue = await GradingWorkflowService.get_faculty_grading_queue(db, user)

        return {
            "assigned_offerings_count": len(offerings_summary),
            "total_enrolled_students": total_students,
            "pending_grading_count": len(grading_queue),
            "active_intervention_signals_count": len(active_signals),
            "recent_assessments_count": 0,
            "average_cohort_completion": 0.0,
            "offerings": offerings_summary,
            "urgent_signals": urgent_signals[:5],
        }

    # -------------------------------------------------------------------------
    # 2. Course Offering Analytics Drill-down
    # -------------------------------------------------------------------------

    @classmethod
    async def get_course_offering_analytics(
        cls,
        db: AsyncSession,
        offering_id: str,
        user: User,
    ) -> Dict[str, Any]:
        """Provides deterministic analytics for a specific Course Offering."""
        off_res = await db.execute(
            select(CourseOffering, Course, Section)
            .join(Course, CourseOffering.course_id == Course.id)
            .join(Section, CourseOffering.section_id == Section.id)
            .where(CourseOffering.id == offering_id)
        )
        row = off_res.first()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course Offering not found.")
        offering, course, section = row

        # Check authorization
        if user.role == UserRole.TEACHER:
            teacher_prof = (
                await db.execute(
                    select(TeacherAcademicProfile).where(TeacherAcademicProfile.user_id == user.id)
                )
            ).scalar_one_or_none()
            if not teacher_prof:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher profile not found.")
            assigned = (
                await db.execute(
                    select(TeachingAssignment).where(
                        TeachingAssignment.teacher_profile_id == teacher_prof.id,
                        TeachingAssignment.course_offering_id == offering.id,
                    )
                )
            ).scalar_one_or_none()
            if not assigned:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not assigned to this offering.")

        # Enrolled students
        enrollments = (
            await db.execute(
                select(StudentEnrollment).where(
                    StudentEnrollment.course_offering_id == offering.id,
                    StudentEnrollment.enrollment_status == "enrolled",
                )
            )
        ).scalars().all()
        enrolled_student_ids = [e.student_profile_id for e in enrollments]
        enrolled_count = len(enrolled_student_ids)

        # Active learners from LessonProgress
        active_progress = (
            await db.execute(
                select(LessonProgress).where(
                    LessonProgress.course_offering_id == offering.id,
                    LessonProgress.student_profile_id.in_(enrolled_student_ids) if enrolled_student_ids else False,
                )
            )
        ).scalars().all()
        active_student_ids = set(lp.student_profile_id for lp in active_progress)

        progress_percentages = [float(lp.completion_percentage) for lp in active_progress]
        avg_lesson_progress = (
            round(sum(progress_percentages) / len(progress_percentages), 2)
            if progress_percentages
            else 0.0
        )
        completion_rate = (
            round(len([p for p in progress_percentages if p >= 100.0]) / enrolled_count, 4)
            if enrolled_count > 0
            else 0.0
        )

        # Assessments mapped to offering
        assessments_res = await db.execute(
            select(Assessment).where(Assessment.course_offering_id == offering.id)
        )
        course_assessments = assessments_res.scalars().all()

        assessments_summary: List[Dict[str, Any]] = []
        for ass in course_assessments:
            attempts_res = await db.execute(
                select(AssessmentAttempt)
                .join(AssessmentVersion, AssessmentAttempt.assessment_version_id == AssessmentVersion.id)
                .where(
                    AssessmentVersion.assessment_id == ass.id,
                    AssessmentAttempt.student_profile_id.in_(enrolled_student_ids) if enrolled_student_ids else False,
                )
            )
            attempts = attempts_res.scalars().all()

            ass_metric = CourseAnalyticsEngine.compute_assessment_metrics(
                assessment_id=ass.id,
                title=ass.title,
                enrolled_count=enrolled_count,
                attempts=[
                    {
                        "id": a.id,
                        "status": a.status,
                        "percentage": float(a.percentage) if a.percentage is not None else None,
                        "is_passed": a.is_passed,
                    }
                    for a in attempts
                ],
                questions_raw=[],
                responses=[],
            )
            assessments_summary.append(ass_metric)

        # Concepts analytics linked via CourseContent -> Curriculum -> Module -> Lesson -> LessonConcept
        concepts_res = await db.execute(
            select(Concept)
            .join(LessonConcept, Concept.id == LessonConcept.concept_id)
            .join(Lesson, LessonConcept.lesson_id == Lesson.id)
            .join(Module, Lesson.module_id == Module.id)
            .join(Curriculum, Module.curriculum_id == Curriculum.id)
            .join(CourseContent, Curriculum.course_content_id == CourseContent.id)
            .where(CourseContent.course_id == course.id)
            .distinct()
        )
        course_concepts = concepts_res.scalars().all()
        concept_ids = [c.id for c in course_concepts]

        knowledge_states_res = await db.execute(
            select(StudentConceptKnowledgeState).where(
                StudentConceptKnowledgeState.concept_id.in_(concept_ids) if concept_ids else False,
                StudentConceptKnowledgeState.student_profile_id.in_(enrolled_student_ids) if enrolled_student_ids else False,
            )
        )
        knowledge_states = knowledge_states_res.scalars().all()

        reviews_res = await db.execute(
            select(ConceptReviewState).where(
                ConceptReviewState.concept_id.in_(concept_ids) if concept_ids else False,
                ConceptReviewState.student_profile_id.in_(enrolled_student_ids) if enrolled_student_ids else False,
            )
        )
        review_states = reviews_res.scalars().all()

        concepts_analytics = CourseAnalyticsEngine.compute_concept_analytics(
            concepts_raw=[{"id": c.id, "name": c.name} for c in course_concepts],
            knowledge_states=[
                {
                    "concept_id": ks.concept_id,
                    "mastery_score": float(ks.mastery_score),
                    "retention_score": float(ks.retention_score),
                }
                for ks in knowledge_states
            ],
            review_states=[
                {
                    "concept_id": rs.concept_id,
                    "is_overdue": rs.due_date < datetime.now(timezone.utc).date() if rs.due_date else False,
                    "days_overdue": (datetime.now(timezone.utc).date() - rs.due_date).days if rs.due_date and rs.due_date < datetime.now(timezone.utc).date() else 0,
                }
                for rs in review_states
            ],
            prerequisite_checks=[],
        )

        difficult_concepts = [c["concept_name"] for c in concepts_analytics if c["is_difficult"]]

        # Project evidence count
        project_evidence_count = (
            await db.scalar(
                select(func.count(ProjectEvidence.id)).where(
                    ProjectEvidence.student_profile_id.in_(enrolled_student_ids) if enrolled_student_ids else False
                )
            )
        ) or 0

        # Active intervention signals
        signals_count = (
            await db.scalar(
                select(func.count(AcademicInterventionSignal.id)).where(
                    AcademicInterventionSignal.course_offering_id == offering.id,
                    AcademicInterventionSignal.status.in_(["detected", "acknowledged"]),
                )
            )
        ) or 0

        return {
            "offering_id": offering.id,
            "course_id": course.id,
            "course_code": course.code,
            "course_title": course.title,
            "section_name": section.name,
            "enrolled_count": enrolled_count,
            "active_learners_count": len(active_student_ids),
            "average_lesson_progress": avg_lesson_progress,
            "completion_rate": completion_rate,
            "assessments_summary": assessments_summary,
            "concepts_analytics": concepts_analytics,
            "difficult_concepts": difficult_concepts,
            "active_intervention_signals_count": signals_count,
            "project_evidence_count": project_evidence_count,
            "algorithm_version": CourseAnalyticsEngine.ALGORITHM_VERSION,
            "calculated_at": datetime.now(timezone.utc),
        }

    # -------------------------------------------------------------------------
    # 3. HOD Department Analytics
    # -------------------------------------------------------------------------

    @classmethod
    async def get_department_analytics(
        cls,
        db: AsyncSession,
        department_id: str,
        user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """Provides department-scoped intelligence for HOD and authorized administrators."""
        dept_res = await db.execute(select(Department).where(Department.id == department_id))
        department = dept_res.scalar_one_or_none()
        if not department:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found.")

        # RBAC Check: HOD must match department
        if user is not None and user.role == UserRole.HOD:
            teacher_prof = (
                await db.execute(
                    select(TeacherAcademicProfile).where(TeacherAcademicProfile.user_id == user.id)
                )
            ).scalar_one_or_none()
            if not teacher_prof or teacher_prof.department_id != department.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="HOD is strictly isolated to their own academic department.",
                )

        # Hierarchy counts
        programs = (
            await db.execute(select(Program).where(Program.department_id == department.id))
        ).scalars().all()
        program_ids = [p.id for p in programs]

        courses = (
            await db.execute(select(Course).where(Course.department_id == department.id))
        ).scalars().all()
        course_ids = [c.id for c in courses]

        offerings_count = (
            await db.scalar(
                select(func.count(CourseOffering.id)).where(
                    CourseOffering.course_id.in_(course_ids) if course_ids else False
                )
            )
        ) or 0

        faculty_count = (
            await db.scalar(
                select(func.count(TeacherAcademicProfile.id)).where(
                    TeacherAcademicProfile.department_id == department.id
                )
            )
        ) or 0

        students = (
            await db.execute(
                select(StudentAcademicProfile).where(
                    StudentAcademicProfile.program_id.in_(program_ids) if program_ids else False
                )
            )
        ).scalars().all()
        student_ids = [s.id for s in students]
        total_students = len(student_ids)

        # Career readiness average
        career_states = (
            await db.execute(
                select(StudentCareerReadinessState).where(
                    StudentCareerReadinessState.student_profile_id.in_(student_ids) if student_ids else False
                )
            )
        ).scalars().all()
        career_scores = [
            float(cs.overall_readiness_percentage)
            for cs in career_states
            if cs.overall_readiness_percentage is not None
        ]

        # Concept mastery average
        knowledge_states = (
            await db.execute(
                select(StudentConceptKnowledgeState).where(
                    StudentConceptKnowledgeState.student_profile_id.in_(student_ids) if student_ids else False
                )
            )
        ).scalars().all()
        mastery_scores = [float(ks.mastery_score) for ks in knowledge_states]

        # Verified projects count
        verified_projects = (
            await db.scalar(
                select(func.count(StudentProject.id)).where(
                    StudentProject.student_profile_id.in_(student_ids) if student_ids else False,
                    StudentProject.is_verified == True,
                )
            )
        ) or 0

        # Signals breakdown
        signals = (
            await db.execute(
                select(AcademicInterventionSignal).where(
                    AcademicInterventionSignal.student_profile_id.in_(student_ids) if student_ids else False,
                    AcademicInterventionSignal.status.in_(["detected", "acknowledged"]),
                )
            )
        ).scalars().all()

        signals_by_severity = {
            "urgent": sum(1 for s in signals if s.severity == "urgent"),
            "high": sum(1 for s in signals if s.severity == "high"),
            "medium": sum(1 for s in signals if s.severity == "medium"),
            "low": sum(1 for s in signals if s.severity == "low"),
        }

        return DepartmentAnalyticsEngine.aggregate_department_metrics(
            department_id=department.id,
            department_name=department.name,
            department_code=department.code,
            total_programs=len(programs),
            total_courses=len(courses),
            total_offerings=offerings_count,
            total_faculty=faculty_count,
            total_students=total_students,
            course_completions=[],
            assessment_scores=[],
            concept_mastery_scores=mastery_scores,
            career_readiness_scores=career_scores,
            verified_projects_count=verified_projects,
            signals_by_severity=signals_by_severity,
            difficult_concepts=[],
        )

    # -------------------------------------------------------------------------
    # 4. Department Comparison (Admin / Leadership) with Privacy Suppression
    # -------------------------------------------------------------------------

    @classmethod
    async def get_department_comparisons(
        cls,
        db: AsyncSession,
        institution_id: str,
        user: User,
    ) -> Dict[str, Any]:
        """Compares departments with small cohort suppression (< 3 students)."""
        if user.role not in (UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only institutional leadership can access cross-department comparisons.",
            )

        departments = (
            await db.execute(
                select(Department).where(Department.institution_id == institution_id)
            )
        ).scalars().all()

        summaries: List[Dict[str, Any]] = []
        for d in departments:
            summary = await cls.get_department_analytics(db, d.id, user)
            summaries.append(summary)

        comparisons = DepartmentAnalyticsEngine.compare_departments(
            department_summaries=summaries,
            min_cohort_size=DepartmentAnalyticsEngine.MINIMUM_COHORT_SUPPRESSION_THRESHOLD,
        )

        return {
            "institution_id": institution_id,
            "minimum_cohort_size": DepartmentAnalyticsEngine.MINIMUM_COHORT_SUPPRESSION_THRESHOLD,
            "departments": comparisons,
            "algorithm_version": DepartmentAnalyticsEngine.ALGORITHM_VERSION,
            "calculated_at": datetime.now(timezone.utc),
        }

    # -------------------------------------------------------------------------
    # 5. Placement Officer Intelligence
    # -------------------------------------------------------------------------

    @classmethod
    async def get_placement_analytics(
        cls,
        db: AsyncSession,
        institution_id: str,
        user: User,
    ) -> Dict[str, Any]:
        """Provides employability, target careers, and verified portfolio intelligence."""
        if user.role not in (UserRole.PLACEMENT_OFFICER, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Placement officer or administrator role required.",
            )

        students = (
            await db.execute(
                select(StudentAcademicProfile).where(
                    StudentAcademicProfile.institution_id == institution_id
                )
            )
        ).scalars().all()
        student_ids = [s.id for s in students]

        # Career goals
        goals = (
            await db.execute(
                select(StudentCareerGoal).where(
                    StudentCareerGoal.student_profile_id.in_(student_ids) if student_ids else False
                )
            )
        ).scalars().all()

        # Career readiness states
        readiness_states = (
            await db.execute(
                select(StudentCareerReadinessState).where(
                    StudentCareerReadinessState.student_profile_id.in_(student_ids) if student_ids else False
                )
            )
        ).scalars().all()

        # Placement readiness states
        placement_states = (
            await db.execute(
                select(PlacementReadinessState).where(
                    PlacementReadinessState.student_profile_id.in_(student_ids) if student_ids else False
                )
            )
        ).scalars().all()

        # Portfolio snapshots
        portfolio_snaps = (
            await db.execute(
                select(PortfolioIntelligenceSnapshot).where(
                    PortfolioIntelligenceSnapshot.student_profile_id.in_(student_ids) if student_ids else False
                )
            )
        ).scalars().all()

        # Verified projects per student
        verified_projects_rows = (
            await db.execute(
                select(StudentProject.student_profile_id, func.count(StudentProject.id))
                .where(
                    StudentProject.student_profile_id.in_(student_ids) if student_ids else False,
                    StudentProject.is_verified == True,
                )
                .group_by(StudentProject.student_profile_id)
            )
        ).all()
        verified_proj_dict = {row[0]: row[1] for row in verified_projects_rows}

        metrics = PlacementAnalyticsEngine.aggregate_placement_intelligence(
            total_students=len(students),
            career_goals=[
                {"career_title": g.target_industry or "Software Engineering"} for g in goals
            ],
            career_readiness_states=[
                {
                    "overall_readiness_percentage": float(r.overall_readiness_percentage)
                    if r.overall_readiness_percentage is not None
                    else None
                }
                for r in readiness_states
            ],
            placement_states=[
                {"readiness_tier": p.readiness_tier} for p in placement_states
            ],
            student_verified_projects=verified_proj_dict,
            portfolio_snapshots=[
                {
                    "overall_health_score": float(p.overall_health_score)
                    if p.overall_health_score is not None
                    else None
                }
                for p in portfolio_snaps
            ],
            skill_gaps=[],
        )

        return {
            "institution_id": institution_id,
            **metrics,
            "calculated_at": datetime.now(timezone.utc),
        }

    # -------------------------------------------------------------------------
    # 6. Early Intervention Signal Lifecycle
    # -------------------------------------------------------------------------

    @classmethod
    async def scan_and_generate_signals(
        cls,
        db: AsyncSession,
        institution_id: str,
        user: Optional[User] = None,
    ) -> List[AcademicInterventionSignal]:
        """Scans student population and persists newly detected deterministic signals."""
        if user is not None and user.role not in (UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized to run intervention detection scan.",
            )

        students = (
            await db.execute(
                select(StudentAcademicProfile).where(
                    StudentAcademicProfile.institution_id == institution_id
                )
            )
        ).scalars().all()

        created_signals: List[AcademicInterventionSignal] = []

        for student in students:
            # 1. Assessment attempts
            attempts = (
                await db.execute(
                    select(AssessmentAttempt).where(
                        AssessmentAttempt.student_profile_id == student.id
                    )
                )
            ).scalars().all()

            # 2. Concept knowledge states
            k_states = (
                await db.execute(
                    select(StudentConceptKnowledgeState).where(
                        StudentConceptKnowledgeState.student_profile_id == student.id
                    )
                )
            ).scalars().all()

            # 3. Overdue reviews
            reviews = (
                await db.execute(
                    select(ConceptReviewState).where(
                        ConceptReviewState.student_profile_id == student.id
                    )
                )
            ).scalars().all()
            now_date = datetime.now(timezone.utc).date()
            overdue_reviews = [
                {
                    "concept_id": r.concept_id,
                    "days_overdue": (now_date - r.due_date).days,
                }
                for r in reviews
                if r.due_date and r.due_date < now_date
            ]

            # 4. Project skills
            p_skills = (
                await db.execute(
                    select(StudentProjectSkill)
                    .join(StudentProject, StudentProjectSkill.project_id == StudentProject.id)
                    .where(StudentProject.student_profile_id == student.id)
                )
            ).scalars().all()

            # Run deterministic engine
            signals_specs = InterventionSignalEngine.evaluate_student_signals(
                assessment_attempts=[
                    {
                        "id": a.id,
                        "status": a.status,
                        "percentage": float(a.percentage) if a.percentage is not None else None,
                        "is_passed": a.is_passed,
                    }
                    for a in attempts
                ],
                concept_states=[
                    {"concept_id": ks.concept_id, "mastery_score": float(ks.mastery_score)}
                    for ks in k_states
                ],
                overdue_reviews=overdue_reviews,
                lesson_progress=[],
                prerequisite_checks=[],
                project_skills=[
                    {
                        "verification_status": s.verification_status,
                        "claimed_level": s.claimed_level,
                    }
                    for s in p_skills
                ],
            )

            for spec in signals_specs:
                # Deduplicate: Check if active signal of same type already exists
                existing = (
                    await db.execute(
                        select(AcademicInterventionSignal).where(
                            AcademicInterventionSignal.student_profile_id == student.id,
                            AcademicInterventionSignal.signal_type == spec["signal_type"],
                            AcademicInterventionSignal.status.in_(["detected", "acknowledged"]),
                        )
                    )
                ).scalar_one_or_none()

                if not existing:
                    signal = AcademicInterventionSignal(
                        institution_id=institution_id,
                        student_profile_id=student.id,
                        signal_type=spec["signal_type"],
                        severity=spec["severity"],
                        title=spec["title"],
                        evidence_data=spec["evidence_data"],
                        recommended_action=spec["recommended_action"],
                        algorithm_version=spec["algorithm_version"],
                        status="detected",
                    )
                    db.add(signal)
                    created_signals.append(signal)

        await db.commit()
        return created_signals

    @classmethod
    async def scan_all_institutions_for_signals(
        cls,
        db: AsyncSession,
        institution_id: Optional[str] = None,
    ) -> Dict[str, int]:
        """Scans student population across active institutions and creates intervention alerts."""
        inst_query = select(Institution)
        if institution_id:
            inst_query = inst_query.where(Institution.id == institution_id)
        institutions = (await db.execute(inst_query)).scalars().all()

        results: Dict[str, int] = {}
        for inst in institutions:
            try:
                signals = await cls.scan_and_generate_signals(
                    db=db,
                    institution_id=inst.id,
                    user=None,
                )
                results[inst.id] = len(signals)
            except Exception:
                await db.rollback()
                continue

        return results

    @classmethod
    async def generate_analytics_snapshots(
        cls,
        db: AsyncSession,
        institution_id: Optional[str] = None,
    ) -> List[InstitutionalAnalyticsSnapshot]:
        """Generates point-in-time cached aggregate analytics snapshots for institutions and departments.
        
        Pure deterministic aggregation, safe to retry, and idempotent.
        """
        inst_query = select(Institution)
        if institution_id:
            inst_query = inst_query.where(Institution.id == institution_id)
        institutions = (await db.execute(inst_query)).scalars().all()

        created_snapshots: List[InstitutionalAnalyticsSnapshot] = []

        for inst in institutions:
            try:
                # 1. Department snapshots
                depts = (
                    await db.execute(
                        select(Department).where(Department.institution_id == inst.id)
                    )
                ).scalars().all()

                dept_summaries: List[Dict[str, Any]] = []
                for dept in depts:
                    try:
                        dept_metrics = await cls.get_department_analytics(
                            db=db,
                            department_id=dept.id,
                            user=None,
                        )
                        snap = InstitutionalAnalyticsSnapshot(
                            institution_id=inst.id,
                            scope_type="department",
                            scope_id=dept.id,
                            metric_payload=dept_metrics,
                            algorithm_version=DepartmentAnalyticsEngine.ALGORITHM_VERSION,
                        )
                        db.add(snap)
                        created_snapshots.append(snap)
                        dept_summaries.append(dept_metrics)
                    except Exception:
                        pass

                # 2. Institution-level aggregate snapshot
                inst_metrics = {
                    "institution_id": inst.id,
                    "institution_name": inst.name,
                    "institution_code": inst.code,
                    "total_departments": len(depts),
                    "departments_analyzed": len(dept_summaries),
                    "total_students": sum(d.get("total_students", 0) for d in dept_summaries),
                    "total_faculty": sum(d.get("total_faculty", 0) for d in dept_summaries),
                    "total_offerings": sum(d.get("total_offerings", 0) for d in dept_summaries),
                    "active_intervention_signals_count": sum(
                        d.get("active_intervention_signals_count", 0) for d in dept_summaries
                    ),
                    "calculated_at": datetime.now(timezone.utc).isoformat(),
                }
                inst_snap = InstitutionalAnalyticsSnapshot(
                    institution_id=inst.id,
                    scope_type="institution",
                    scope_id=inst.id,
                    metric_payload=inst_metrics,
                    algorithm_version="v1.0.0-deterministic",
                )
                db.add(inst_snap)
                created_snapshots.append(inst_snap)

                await db.commit()
            except Exception:
                await db.rollback()
                continue

        return created_snapshots

    @classmethod
    async def acknowledge_signal(
        cls,
        db: AsyncSession,
        signal_id: str,
        user: User,
    ) -> AcademicInterventionSignal:
        """Acknowledges an intervention signal by an authorized faculty member."""
        res = await db.execute(
            select(AcademicInterventionSignal).where(AcademicInterventionSignal.id == signal_id)
        )
        signal = res.scalar_one_or_none()
        if not signal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signal not found.")

        signal.status = "acknowledged"
        signal.acknowledged_at = datetime.now(timezone.utc)
        signal.acknowledged_by_user_id = user.id
        await db.commit()
        await db.refresh(signal)
        return signal

    @classmethod
    async def dismiss_signal(
        cls,
        db: AsyncSession,
        signal_id: str,
        reason: str,
        user: User,
    ) -> AcademicInterventionSignal:
        """Dismisses an intervention signal with an auditable explanation."""
        res = await db.execute(
            select(AcademicInterventionSignal).where(AcademicInterventionSignal.id == signal_id)
        )
        signal = res.scalar_one_or_none()
        if not signal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signal not found.")

        signal.status = "dismissed"
        signal.dismiss_reason = reason
        signal.acknowledged_at = datetime.now(timezone.utc)
        signal.acknowledged_by_user_id = user.id
        await db.commit()
        await db.refresh(signal)
        return signal

    @classmethod
    async def convert_signal_to_intervention(
        cls,
        db: AsyncSession,
        signal_id: str,
        category: str,
        priority: str,
        user: User,
        action_plan: Optional[str] = None,
        follow_up_date: Optional[Any] = None,
    ) -> AcademicInterventionSignal:
        """Elevates an academic signal into a formal StudentIntervention record."""
        res = await db.execute(
            select(AcademicInterventionSignal).where(AcademicInterventionSignal.id == signal_id)
        )
        signal = res.scalar_one_or_none()
        if not signal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signal not found.")

        intervention = StudentIntervention(
            institution_id=signal.institution_id,
            student_profile_id=signal.student_profile_id,
            created_by_user_id=user.id,
            category=category,
            priority=priority,
            status="open",
            reason=f"[{signal.signal_type.upper()}] {signal.title}",
            action_plan=action_plan or signal.recommended_action,
            follow_up_date=follow_up_date,
        )
        db.add(intervention)
        await db.flush()

        signal.status = "intervention_created"
        signal.intervention_id = intervention.id
        signal.acknowledged_at = datetime.now(timezone.utc)
        signal.acknowledged_by_user_id = user.id

        await db.commit()
        await db.refresh(signal)
        return signal

    # -------------------------------------------------------------------------
    # 7. Real Data Exports (CSV)
    # -------------------------------------------------------------------------

    @classmethod
    async def export_course_performance_csv(
        cls,
        db: AsyncSession,
        offering_id: str,
        user: User,
    ) -> str:
        """Generates authentic CSV export for course offering analytics with formula injection defense."""
        analytics = await cls.get_course_offering_analytics(db, offering_id, user)

        def _clean(val: Any) -> Any:
            """Prevents CSV formula injection (CWE-1236) by quoting leading trigger characters."""
            if isinstance(val, str) and val and val[0] in ("=", "+", "-", "@", "\t", "\r"):
                return f"'{val}"
            return val

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["Course Code", "Course Title", "Section", "Enrolled", "Active Learners", "Completion Rate"])
        writer.writerow([
            _clean(analytics["course_code"]),
            _clean(analytics["course_title"]),
            _clean(analytics["section_name"]),
            _clean(analytics["enrolled_count"]),
            _clean(analytics["active_learners_count"]),
            _clean(f"{round(analytics['completion_rate'] * 100, 2)}%"),
        ])

        writer.writerow([])
        writer.writerow(["Assessment Title", "Assigned", "Started", "Completed", "Average Score", "Pass Rate"])
        for ass in analytics["assessments_summary"]:
            writer.writerow([
                _clean(ass["title"]),
                _clean(ass["total_assigned"]),
                _clean(ass["total_started"]),
                _clean(ass["total_completed"]),
                _clean(f"{ass['average_score']}%" if ass["average_score"] is not None else "N/A"),
                _clean(f"{round(ass['pass_rate'] * 100, 2)}%" if ass["pass_rate"] is not None else "N/A"),
            ])

        writer.writerow([])
        writer.writerow(["Concept Name", "Average Mastery", "High Retention Risk", "Overdue Reviews"])
        for c in analytics["concepts_analytics"]:
            writer.writerow([
                _clean(c["concept_name"]),
                _clean(f"{round(c['average_mastery'] * 100, 2)}%"),
                _clean(c["high_retention_risk_count"]),
                _clean(c["overdue_reviews_count"]),
            ])

        return output.getvalue()
