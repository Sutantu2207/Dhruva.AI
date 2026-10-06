"""Pure deterministic Career Trajectory Engine for Domain 7."""

from decimal import Decimal
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from app.domains.career_intelligence.readiness_engine import SkillGapItem


class TrajectoryStepDraft(BaseModel):
    step_number: int
    skill_id: str
    skill_name: str
    title: str
    step_type: str  # concept_mastery, lesson, course, practice, project, assessment
    priority: str  # critical, high, medium, low
    status: str  # not_started, in_progress, completed, blocked, not_available
    target_proficiency: Decimal
    current_proficiency: Decimal
    gap_size: Decimal
    reference_course_id: Optional[str] = None
    reference_lesson_id: Optional[str] = None
    reference_concept_id: Optional[str] = None
    reference_assessment_id: Optional[str] = None
    explanation: str


class TrajectoryDraftResult(BaseModel):
    career_id: str
    career_title: str
    status: str  # not_started, in_progress, completed, blocked
    steps: List[TrajectoryStepDraft]
    total_steps: int
    completed_steps: int
    algorithm_version: str


class CareerTrajectoryEngine:
    """Deterministically sequences learning milestones from career skill gaps and canonical catalog links."""

    def __init__(self, algorithm_version: str = "v1"):
        self.algorithm_version = algorithm_version

    def build_trajectory(
        self,
        career_id: str,
        career_title: str,
        gaps: List[SkillGapItem],
        skill_to_concept_map: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        skill_to_lesson_map: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        skill_to_assessment_map: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        concept_readiness_map: Optional[Dict[str, Decimal]] = None,
    ) -> TrajectoryDraftResult:
        """Sequences a progressive career trajectory addressing critical gaps first.

        Invariants:
        1. Critical gaps are ordered ahead of high/medium gaps.
        2. If prerequisite readiness for an underlying concept is weak, step is flagged as 'blocked'.
        3. If no learning resource exists, step is marked 'not_available' without hallucinating content.
        """
        c_map = skill_to_concept_map or {}
        l_map = skill_to_lesson_map or {}
        a_map = skill_to_assessment_map or {}
        r_map = concept_readiness_map or {}

        # Filter gaps where gap_size > 0
        actionable_gaps = [g for g in gaps if g.gap_size > Decimal("0.0000")]

        # Sort priority: critical (0), high (1), medium (2), low (3)
        severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3, "no_gap": 4}
        actionable_gaps.sort(key=lambda x: (severity_rank.get(x.severity, 3), -x.gap_size))

        steps: List[TrajectoryStepDraft] = []
        step_idx = 1
        completed_count = 0

        for gap in actionable_gaps:
            concepts = c_map.get(gap.skill_id, [])
            lessons = l_map.get(gap.skill_id, [])
            assessments = a_map.get(gap.skill_id, [])

            ref_concept_id = concepts[0]["id"] if concepts else None
            ref_lesson_id = lessons[0]["id"] if lessons else None
            ref_course_id = lessons[0].get("course_id") if lessons else None
            ref_assessment_id = assessments[0]["id"] if assessments else None

            # Determine readiness / blocking condition
            is_blocked = False
            if ref_concept_id and ref_concept_id in r_map:
                if r_map[ref_concept_id] < Decimal("0.5000"):
                    is_blocked = True

            # Determine content availability
            has_content = bool(concepts or lessons or assessments)
            if not has_content:
                step_status = "not_available"
                title = f"Study {gap.skill_name} (No mapped learning content available yet)"
                step_type = "practice"
                explanation = "Canonical curriculum mapping currently lacks direct lesson or assessment resources."
            elif is_blocked:
                step_status = "blocked"
                title = f"Strengthen Prerequisites for {gap.skill_name}"
                step_type = "concept_mastery"
                explanation = "Upstream concept prerequisites are weak; complete foundational concepts first."
            elif gap.current_proficiency >= Decimal("0.4000") and ref_assessment_id:
                step_status = "not_started"
                title = f"Verify {gap.skill_name} Competency (Assessment)"
                step_type = "assessment"
                explanation = "Proficiency is developing; take placement benchmark assessment to achieve verified status."
            elif ref_lesson_id:
                step_status = "not_started"
                title = f"Complete Lessons in {gap.skill_name}"
                step_type = "lesson"
                explanation = "Work through structured curriculum modules."
            elif ref_concept_id:
                step_status = "not_started"
                title = f"Master Core Concept: {concepts[0].get('name', gap.skill_name)}"
                step_type = "concept_mastery"
                explanation = "Engage in active recall and practice exercises."
            else:
                step_status = "not_started"
                title = f"Practice {gap.skill_name}"
                step_type = "practice"
                explanation = "Self-directed application and problem sets."

            steps.append(
                TrajectoryStepDraft(
                    step_number=step_idx,
                    skill_id=gap.skill_id,
                    skill_name=gap.skill_name,
                    title=title,
                    step_type=step_type,
                    priority=gap.severity if gap.severity != "no_gap" else "low",
                    status=step_status,
                    target_proficiency=gap.required_proficiency,
                    current_proficiency=gap.current_proficiency,
                    gap_size=gap.gap_size,
                    reference_course_id=ref_course_id,
                    reference_lesson_id=ref_lesson_id,
                    reference_concept_id=ref_concept_id,
                    reference_assessment_id=ref_assessment_id,
                    explanation=explanation,
                )
            )
            step_idx += 1

        overall_status = "completed" if len(steps) == 0 else "in_progress"

        return TrajectoryDraftResult(
            career_id=career_id,
            career_title=career_title,
            status=overall_status,
            steps=steps,
            total_steps=len(steps),
            completed_steps=completed_count,
            algorithm_version=self.algorithm_version,
        )
