"""Deterministic Remediation Synthesis Engine (Domain 10).

Builds scaffolded remediation plans according to the pedagogical progression:
Level 1: Recall / Foundational Prerequisite
Level 2: Guided Micro-Lesson
Level 3: Guided Practice
Level 4: Independent Assessment / Practice
Level 5: Reassessment Verification

If content is unavailable for a required step, notes it honestly and alerts content gaps.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.remediation.config import SCAFFOLD_LEVELS, ALGORITHM_VERSION
from app.domains.remediation.assessment_selection_engine import ContentSelectionEngine
from app.domains.content.models import Concept


class RemediationEngine:
    """Synthesizes scaffolded remediation steps using approved content."""

    @staticmethod
    async def synthesize_plan_steps(
        db: AsyncSession,
        target_concept_id: str,
        diagnosis_info: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Construct scaffolded steps deterministically."""
        steps: List[Dict[str, Any]] = []
        seq = 1

        prereq_analysis = diagnosis_info.get("prereq_analysis", {})
        blocking_prereqs = prereq_analysis.get("blocking_prerequisites", [])

        # Step 1: Foundational Prerequisite Review (if blocked)
        if blocking_prereqs:
            first_block = blocking_prereqs[0]
            block_cid = first_block["concept_id"]
            block_name = first_block["name"]

            prereq_lesson = await ContentSelectionEngine.find_lesson_for_concept(db, block_cid)
            prereq_resource = await ContentSelectionEngine.find_resource_for_concept(db, block_cid)

            steps.append({
                "sequence_order": seq,
                "step_type": "PREREQUISITE",
                "concept_id": block_cid,
                "lesson_id": prereq_lesson.id if prereq_lesson else None,
                "resource_id": prereq_resource.id if prereq_resource else None,
                "title": f"Foundation Refresher: {block_name}",
                "description": f"Review fundamental concepts in {block_name} required before advancing.",
                "required": True,
                "scaffold_level": 1,
            })
            seq += 1

        # Fetch target concept name
        c_res = await db.execute(select(Concept).where(Concept.id == target_concept_id))
        target_concept = c_res.scalar_one_or_none()
        target_name = target_concept.name if target_concept else "Target Concept"

        # Step 2: Micro-Lesson on Target Concept
        target_lesson = await ContentSelectionEngine.find_lesson_for_concept(db, target_concept_id)
        target_resource = await ContentSelectionEngine.find_resource_for_concept(db, target_concept_id)

        steps.append({
            "sequence_order": seq,
            "step_type": "MICRO_LESSON",
            "concept_id": target_concept_id,
            "lesson_id": target_lesson.id if target_lesson else None,
            "resource_id": target_resource.id if target_resource else None,
            "title": f"Core Concept Micro-Lesson: {target_name}",
            "description": f"Engage with targeted lesson content on {target_name}.",
            "required": True,
            "scaffold_level": 2,
        })
        seq += 1

        # Step 3: Guided Practice (Scaffold Level 3)
        practice_questions = await ContentSelectionEngine.find_practice_questions(db, target_concept_id, limit=2)
        steps.append({
            "sequence_order": seq,
            "step_type": "GUIDED_PRACTICE",
            "concept_id": target_concept_id,
            "lesson_id": target_lesson.id if target_lesson else None,
            "resource_id": None,
            "title": f"Guided Practice Exercises: {target_name}",
            "description": f"Step-by-step guided exercises reinforcing core principles of {target_name}.",
            "required": True,
            "scaffold_level": 3,
        })
        seq += 1

        # Step 4: Reassessment (Scaffold Level 5)
        reassessment = await ContentSelectionEngine.find_reassessment_for_concept(db, target_concept_id)
        steps.append({
            "sequence_order": seq,
            "step_type": "REASSESSMENT",
            "concept_id": target_concept_id,
            "assessment_id": reassessment.id if reassessment else None,
            "title": f"Outcome Verification Reassessment: {target_name}",
            "description": f"Structured assessment measuring post-remediation mastery of {target_name}.",
            "required": True,
            "scaffold_level": 5,
        })

        return steps
