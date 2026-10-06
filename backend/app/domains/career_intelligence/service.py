"""Transactional service for Domain 7: Skill Intelligence, Career Trajectories & Placement Readiness."""

from decimal import Decimal
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.domains.career_intelligence.models import (
    StudentSkillIntelligenceState,
    StudentSkillEvidenceRecord,
    StudentCareerReadinessState,
    CareerTrajectory,
    CareerTrajectoryStep,
    PlacementReadinessState,
)
from app.domains.career_intelligence.config import DEFAULT_CAREER_CONFIG
from app.domains.career_intelligence.skill_engine import (
    SkillIntelligenceEngine,
    SkillEvidenceInput,
    EvaluatedSkillResult,
)
from app.domains.career_intelligence.readiness_engine import (
    CareerReadinessEngine,
    CareerSkillReq,
    CareerReadinessCalculationResult,
)
from app.domains.career_intelligence.trajectory_engine import (
    CareerTrajectoryEngine,
    TrajectoryDraftResult,
)
from app.domains.career_intelligence.placement_engine import (
    PlacementReadinessEngine,
    PlacementEvaluationInput,
    PlacementReadinessResult,
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
    StudentCertification,
)
from app.domains.assessment.models import SkillEvidence, AssessmentResult, AssessmentAttempt
from app.domains.content.models import ConceptSkill, LessonSkill, CourseSkill, Lesson, Concept
from app.domains.mastery.models import StudentConceptKnowledgeState


class CareerIntelligenceService:
    """Coordinates evidence ingestion, deterministic skill calculation, and career trajectory generation."""

    def __init__(self):
        self.config = DEFAULT_CAREER_CONFIG
        self.skill_engine = SkillIntelligenceEngine(self.config)
        self.readiness_engine = CareerReadinessEngine(self.config)
        self.trajectory_engine = CareerTrajectoryEngine(self.config.algorithm_version)
        self.placement_engine = PlacementReadinessEngine(self.config.algorithm_version)

    async def evaluate_all_student_skills(
        self,
        db: AsyncSession,
        student_profile_id: str,
    ) -> Dict[str, StudentSkillIntelligenceState]:
        """Aggregates all multi-source learning evidence for a student and recomputes authoritative skill states.

        Sources ingested:
        - Domain 5 SkillEvidence
        - Domain 6 StudentConceptKnowledgeState via ConceptSkill mapping
        - Domain 3 StudentProject & StudentProjectSkill
        - Domain 3 StudentSkill (self-reports and verification flags)
        """
        now = datetime.now(timezone.utc)

        # 1. Fetch Domain 5 SkillEvidence
        ev_stmt = select(SkillEvidence).where(SkillEvidence.student_profile_id == student_profile_id)
        ev_records = (await db.execute(ev_stmt)).scalars().all()

        # Group by skill_id
        skill_evidence_map: Dict[str, List[SkillEvidenceInput]] = {}
        for ev in ev_records:
            item = SkillEvidenceInput(
                source_type=ev.evidence_type or "assessment",
                source_id=ev.id,
                score=Decimal(str(ev.score)),
                is_verified=True,  # Domain 5 assessment evaluation is verified by definition
                weight_multiplier=Decimal(str(ev.weight)) if ev.weight else Decimal("1.00"),
            )
            skill_evidence_map.setdefault(ev.skill_id, []).append(item)

        # 2. Fetch Domain 3 Project Skills
        proj_stmt = (
            select(StudentProjectSkill, StudentProject)
            .join(StudentProject, StudentProjectSkill.project_id == StudentProject.id)
            .where(StudentProject.student_profile_id == student_profile_id)
        )
        proj_pairs = (await db.execute(proj_stmt)).all()
        for p_skill, proj in proj_pairs:
            # Score: completed project is 0.85, in_progress is 0.50
            score = Decimal("0.8500") if proj.status == "completed" else Decimal("0.5000")
            item = SkillEvidenceInput(
                source_type="project",
                source_id=proj.id,
                score=score,
                is_verified=proj.is_verified,
                weight_multiplier=Decimal("1.00"),
            )
            skill_evidence_map.setdefault(p_skill.skill_catalog_id, []).append(item)

        # 3. Fetch Domain 6 Concept Knowledge States contributing to skills via ConceptSkill
        cs_stmt = select(ConceptSkill)
        all_cs = (await db.execute(cs_stmt)).scalars().all()
        concept_to_skills: Dict[str, List[Tuple[str, Decimal]]] = {}
        for cs in all_cs:
            concept_to_skills.setdefault(cs.concept_id, []).append((cs.skill_id, Decimal(str(cs.weight))))

        concept_ids = list(concept_to_skills.keys())
        skill_concept_mastery_contrib: Dict[str, Decimal] = {}
        if concept_ids:
            ks_stmt = select(StudentConceptKnowledgeState).where(
                and_(
                    StudentConceptKnowledgeState.student_profile_id == student_profile_id,
                    StudentConceptKnowledgeState.concept_id.in_(concept_ids),
                    StudentConceptKnowledgeState.current_mastery.is_not(None),
                )
            )
            k_states = (await db.execute(ks_stmt)).scalars().all()
            for ks in k_states:
                for skill_id, weight in concept_to_skills.get(ks.concept_id, []):
                    m_val = Decimal(str(ks.current_mastery))
                    # Take maximum or weighted contribution
                    if skill_id not in skill_concept_mastery_contrib or m_val > skill_concept_mastery_contrib[skill_id]:
                        skill_concept_mastery_contrib[skill_id] = m_val

        # 4. Fetch Domain 3 StudentSkill (self-reports)
        ss_stmt = select(StudentSkill).where(StudentSkill.student_profile_id == student_profile_id)
        student_skills = (await db.execute(ss_stmt)).scalars().all()
        self_reports: Dict[str, Decimal] = {}
        for ss in student_skills:
            prof_map = {
                "beginner": Decimal("0.2500"),
                "developing": Decimal("0.4500"),
                "intermediate": Decimal("0.6000"),
                "advanced": Decimal("0.8000"),
                "expert": Decimal("0.9500"),
            }
            sr_val = prof_map.get(ss.proficiency.lower(), Decimal("0.3000"))
            self_reports[ss.skill_catalog_id] = sr_val
            if ss.is_verified:
                skill_evidence_map.setdefault(ss.skill_catalog_id, []).append(
                    SkillEvidenceInput(
                        source_type="faculty_verification",
                        source_id=ss.id,
                        score=sr_val,
                        is_verified=True,
                    )
                )

        # Collect union of all skills touched by evidence or declared
        all_skill_ids = set(skill_evidence_map.keys()) | set(skill_concept_mastery_contrib.keys()) | set(self_reports.keys())

        # Load existing state records to update
        existing_stmt = select(StudentSkillIntelligenceState).where(
            StudentSkillIntelligenceState.student_profile_id == student_profile_id
        )
        existing_states = {s.skill_id: s for s in (await db.execute(existing_stmt)).scalars().all()}

        results: Dict[str, StudentSkillIntelligenceState] = {}

        for skill_id in all_skill_ids:
            ev_list = skill_evidence_map.get(skill_id, [])
            sr = self_reports.get(skill_id)
            c_mastery = skill_concept_mastery_contrib.get(skill_id)

            eval_res = self.skill_engine.evaluate_skill(
                skill_id=skill_id,
                evidence_items=ev_list,
                self_reported_proficiency=sr,
                concept_mastery_score=c_mastery,
            )

            state = existing_states.get(skill_id)
            if not state:
                state = StudentSkillIntelligenceState(
                    student_profile_id=student_profile_id,
                    skill_id=skill_id,
                )
                db.add(state)

            state.observed_proficiency = eval_res.observed_proficiency
            state.self_reported_proficiency = eval_res.self_reported_proficiency
            state.verified_proficiency = eval_res.verified_proficiency
            state.confidence = eval_res.confidence
            state.evidence_count = eval_res.evidence_count
            state.verified_evidence_count = eval_res.verified_evidence_count
            state.assessment_evidence_count = eval_res.assessment_evidence_count
            state.project_evidence_count = eval_res.project_evidence_count
            state.course_evidence_count = eval_res.course_evidence_count
            state.certification_evidence_count = eval_res.certification_evidence_count
            state.concept_mastery_contribution = eval_res.concept_mastery_contribution
            state.verification_status = eval_res.verification_status
            state.proficiency_tier = eval_res.proficiency_tier
            state.algorithm_version = eval_res.algorithm_version
            state.last_evaluated_at = now

            results[skill_id] = state

        await db.flush()
        return results

    async def evaluate_career_readiness(
        self,
        db: AsyncSession,
        student_profile_id: str,
        career_id: Optional[str] = None,
    ) -> Tuple[StudentCareerReadinessState, CareerReadinessCalculationResult]:
        """Calculates deterministic career readiness, gaps, and coverage against canonical CareerSkillMapping."""
        now = datetime.now(timezone.utc)

        # Ensure skill states are computed
        skill_states = await self.evaluate_all_student_skills(db, student_profile_id)

        # Resolve target career if not supplied
        target_career: Optional[CareerCatalog] = None
        is_target_goal = False

        if career_id:
            c_stmt = select(CareerCatalog).where(CareerCatalog.id == career_id)
            target_career = (await db.execute(c_stmt)).scalar_one_or_none()
        else:
            # Check student career goals
            cg_stmt = (
                select(StudentCareerGoal, CareerCatalog)
                .join(CareerCatalog, StudentCareerGoal.career_catalog_id == CareerCatalog.id)
                .where(StudentCareerGoal.student_profile_id == student_profile_id)
                .order_by(StudentCareerGoal.priority.asc())
            )
            goal_pair = (await db.execute(cg_stmt)).first()
            if goal_pair:
                target_career = goal_pair[1]
                is_target_goal = True
            else:
                # Fallback to first available active CareerCatalog entry
                first_c = (await db.execute(select(CareerCatalog).where(CareerCatalog.status == "active"))).scalars().first()
                target_career = first_c

        if not target_career:
            # No catalog career available
            state = StudentCareerReadinessState(
                student_profile_id=student_profile_id,
                career_id="",
                readiness_score=Decimal("0.0000"),
                fit_score=Decimal("0.0000"),
                confidence=Decimal("0.0000"),
                status="insufficient_catalog_data",
                has_sufficient_catalog_data=False,
                algorithm_version=self.config.algorithm_version,
                last_evaluated_at=now,
            )
            calc_res = CareerReadinessCalculationResult(
                career_id="",
                career_title="No Career Configured",
                readiness_score=Decimal("0.0000"),
                fit_score=Decimal("0.0000"),
                confidence=Decimal("0.0000"),
                required_skill_coverage=Decimal("0.0000"),
                preferred_skill_coverage=Decimal("0.0000"),
                critical_skill_coverage=Decimal("0.0000"),
                gaps=[],
                critical_gaps=[],
                strengths=[],
                developing=[],
                status="insufficient_catalog_data",
                explanation={"error": "No career catalog entries exist in database."},
                algorithm_version=self.config.algorithm_version,
            )
            return state, calc_res

        # Fetch canonical career requirements
        mapping_stmt = (
            select(CareerSkillMapping, SkillCatalog)
            .join(SkillCatalog, CareerSkillMapping.skill_id == SkillCatalog.id)
            .where(CareerSkillMapping.career_id == target_career.id)
        )
        mappings = (await db.execute(mapping_stmt)).all()

        reqs: List[CareerSkillReq] = []
        for m, skill in mappings:
            min_prof = Decimal("0.6000") if m.importance in ["required", "critical"] else Decimal("0.4000")
            reqs.append(
                CareerSkillReq(
                    skill_id=m.skill_id,
                    skill_name=skill.name,
                    importance=m.importance,
                    weight=Decimal(str(m.weight)),
                    min_proficiency=min_prof,
                )
            )

        # Build skill proficiency map: prefer verified proficiency, fall back to observed
        proficiencies = {}
        confidences = {}
        for s_id, st in skill_states.items():
            eff_prof = st.verified_proficiency if st.verified_evidence_count > 0 else st.observed_proficiency
            proficiencies[s_id] = eff_prof
            confidences[s_id] = st.confidence

        calc_res = self.readiness_engine.calculate_readiness(
            career_id=target_career.id,
            career_title=target_career.title,
            requirements=reqs,
            student_skill_proficiencies=proficiencies,
            student_skill_confidences=confidences,
            is_target_career_goal=is_target_goal,
        )

        # Upsert StudentCareerReadinessState
        c_state_stmt = select(StudentCareerReadinessState).where(
            and_(
                StudentCareerReadinessState.student_profile_id == student_profile_id,
                StudentCareerReadinessState.career_id == target_career.id,
            )
        )
        c_state = (await db.execute(c_state_stmt)).scalar_one_or_none()
        if not c_state:
            c_state = StudentCareerReadinessState(
                student_profile_id=student_profile_id,
                career_id=target_career.id,
            )
            db.add(c_state)

        c_state.readiness_score = calc_res.readiness_score
        c_state.fit_score = calc_res.fit_score
        c_state.confidence = calc_res.confidence
        c_state.required_skill_coverage = calc_res.required_skill_coverage
        c_state.preferred_skill_coverage = calc_res.preferred_skill_coverage
        c_state.critical_skill_coverage = calc_res.critical_skill_coverage
        c_state.critical_gaps_count = len(calc_res.critical_gaps)
        c_state.strengths_count = len(calc_res.strengths)
        c_state.developing_count = len(calc_res.developing)
        c_state.has_sufficient_catalog_data = len(reqs) > 0
        c_state.status = calc_res.status
        c_state.explanation_breakdown = calc_res.explanation
        c_state.algorithm_version = calc_res.algorithm_version
        c_state.last_evaluated_at = now

        await db.flush()
        return c_state, calc_res

    async def generate_career_trajectory(
        self,
        db: AsyncSession,
        student_profile_id: str,
        career_id: Optional[str] = None,
    ) -> CareerTrajectory:
        """Constructs an actionable career trajectory mapped to canonical course, lesson, and concept resources."""
        now = datetime.now(timezone.utc)

        # Evaluate readiness to identify skill gaps
        c_state, calc_res = await self.evaluate_career_readiness(db, student_profile_id, career_id)

        target_career_id = c_state.career_id
        if not target_career_id:
            # Fallback if no career
            traj = CareerTrajectory(
                student_profile_id=student_profile_id,
                career_id="",
                status="not_available",
                total_steps=0,
                completed_steps=0,
            )
            return traj

        # Load canonical mappings from skills to concepts, lessons, and courses
        actionable_skill_ids = [g.skill_id for g in calc_res.gaps if g.gap_size > Decimal("0.0000")]

        skill_to_concept: Dict[str, List[Dict[str, Any]]] = {}
        if actionable_skill_ids:
            cs_stmt = (
                select(ConceptSkill, Concept)
                .join(Concept, ConceptSkill.concept_id == Concept.id)
                .where(ConceptSkill.skill_id.in_(actionable_skill_ids))
            )
            for cs, c in (await db.execute(cs_stmt)).all():
                skill_to_concept.setdefault(cs.skill_id, []).append({"id": c.id, "name": c.name})

        skill_to_lesson: Dict[str, List[Dict[str, Any]]] = {}
        if actionable_skill_ids:
            ls_stmt = (
                select(LessonSkill, Lesson)
                .join(Lesson, LessonSkill.lesson_id == Lesson.id)
                .where(LessonSkill.skill_id.in_(actionable_skill_ids))
            )
            for ls, les in (await db.execute(ls_stmt)).all():
                skill_to_lesson.setdefault(ls.skill_id, []).append(
                    {"id": les.id, "title": les.title, "course_id": les.course_content_id}
                )

        # Load prerequisite readiness for concepts from Domain 6
        concept_readiness: Dict[str, Decimal] = {}
        all_c_ids = [c["id"] for clist in skill_to_concept.values() for c in clist]
        if all_c_ids:
            ks_stmt = select(StudentConceptKnowledgeState).where(
                and_(
                    StudentConceptKnowledgeState.student_profile_id == student_profile_id,
                    StudentConceptKnowledgeState.concept_id.in_(all_c_ids),
                )
            )
            for ks in (await db.execute(ks_stmt)).scalars().all():
                if ks.prerequisite_readiness is not None:
                    concept_readiness[ks.concept_id] = Decimal(str(ks.prerequisite_readiness))

        # Build trajectory via deterministic engine
        draft = self.trajectory_engine.build_trajectory(
            career_id=target_career_id,
            career_title=calc_res.career_title,
            gaps=calc_res.gaps,
            skill_to_concept_map=skill_to_concept,
            skill_to_lesson_map=skill_to_lesson,
            concept_readiness_map=concept_readiness,
        )

        # Upsert CareerTrajectory
        traj_stmt = (
            select(CareerTrajectory)
            .options(selectinload(CareerTrajectory.steps))
            .where(
                and_(
                    CareerTrajectory.student_profile_id == student_profile_id,
                    CareerTrajectory.career_id == target_career_id,
                )
            )
        )
        traj = (await db.execute(traj_stmt)).scalar_one_or_none()
        if not traj:
            traj = CareerTrajectory(
                student_profile_id=student_profile_id,
                career_id=target_career_id,
            )
            db.add(traj)
            await db.flush()
        else:
            # Clear old steps
            for s in list(traj.steps):
                await db.delete(s)
            await db.flush()

        traj.status = draft.status
        traj.total_steps = draft.total_steps
        traj.completed_steps = draft.completed_steps
        traj.algorithm_version = draft.algorithm_version

        # Add steps
        for step_d in draft.steps:
            step_record = CareerTrajectoryStep(
                trajectory_id=traj.id,
                step_number=step_d.step_number,
                skill_id=step_d.skill_id,
                title=step_d.title,
                step_type=step_d.step_type,
                priority=step_d.priority,
                status=step_d.status,
                target_proficiency=step_d.target_proficiency,
                current_proficiency=step_d.current_proficiency,
                gap_size=step_d.gap_size,
                reference_course_id=step_d.reference_course_id,
                reference_lesson_id=step_d.reference_lesson_id,
                reference_concept_id=step_d.reference_concept_id,
                reference_assessment_id=step_d.reference_assessment_id,
            )
            db.add(step_record)

        await db.flush()
        # Reload with steps
        traj = (await db.execute(traj_stmt)).scalar_one()
        return traj

    async def evaluate_placement_readiness(
        self,
        db: AsyncSession,
        student_profile_id: str,
    ) -> PlacementReadinessState:
        """Evaluates multi-component placement readiness honestly. Unassessed components are explicitly labeled NOT_ASSESSED."""
        now = datetime.now(timezone.utc)

        # 1. Technical readiness from primary career
        c_state, _ = await self.evaluate_career_readiness(db, student_profile_id)
        tech_score = c_state.readiness_score if c_state.has_sufficient_catalog_data else None

        # 2. Average assessment score from Domain 5
        asst_stmt = (
            select(func.avg(AssessmentResult.percentage))
            .join(AssessmentAttempt, AssessmentResult.attempt_id == AssessmentAttempt.id)
            .where(AssessmentAttempt.student_profile_id == student_profile_id)
        )
        avg_pct = (await db.execute(asst_stmt)).scalar()
        asst_score = Decimal(str(avg_pct / 100.0)) if avg_pct is not None else None

        # 3. Verified projects from Domain 3
        proj_stmt = select(StudentProject).where(
            and_(
                StudentProject.student_profile_id == student_profile_id,
                StudentProject.is_verified == True,
            )
        )
        verified_projects = (await db.execute(proj_stmt)).scalars().all()
        proj_count = len(verified_projects)

        # 4. Check target goal match
        cg_stmt = select(StudentCareerGoal).where(StudentCareerGoal.student_profile_id == student_profile_id)
        has_career_goal = bool((await db.execute(cg_stmt)).scalars().first())

        # Build input
        eval_in = PlacementEvaluationInput(
            career_readiness_score=tech_score,
            average_assessment_score=asst_score,
            verified_projects_count=proj_count,
            project_score_average=Decimal("0.8000") if proj_count >= 2 else (Decimal("0.6000") if proj_count == 1 else None),
            communication_score=None,  # Not yet assessed in verified assessment battery
            resume_score=None,         # Not yet assessed by career services
            interview_score=None,      # Not yet assessed in mock interview
            career_goal_match=has_career_goal,
        )

        p_res = self.placement_engine.evaluate_placement_readiness(eval_in)

        # Upsert PlacementReadinessState
        p_stmt = select(PlacementReadinessState).where(PlacementReadinessState.student_profile_id == student_profile_id)
        p_state = (await db.execute(p_stmt)).scalar_one_or_none()
        if not p_state:
            p_state = PlacementReadinessState(student_profile_id=student_profile_id)
            db.add(p_state)

        p_state.career_id = c_state.career_id if c_state.career_id else None
        p_state.technical_readiness = p_res.technical_readiness
        p_state.assessment_readiness = p_res.assessment_readiness
        p_state.project_evidence_score = p_res.project_evidence_score
        p_state.communication_readiness = p_res.communication_readiness
        p_state.resume_readiness = p_res.resume_readiness
        p_state.interview_readiness = p_res.interview_readiness
        p_state.career_alignment = p_res.career_alignment
        p_state.overall_status = p_res.overall_status
        p_state.component_statuses = p_res.component_statuses
        p_state.algorithm_version = p_res.algorithm_version
        p_state.updated_at = now

        await db.flush()
        return p_state


career_intelligence_service = CareerIntelligenceService()
