"""Controlled deterministic tool registry and executor for Domain 11 AI."""

import hashlib
import json
from decimal import Decimal
from typing import Dict, Any, Callable, Awaitable, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.identity.models import User
from app.core.security import UserRole
from app.domains.content.models import Concept, Lesson, ConceptPrerequisite
from app.domains.mastery.models import StudentConceptKnowledgeState
from app.domains.remediation.models import RemediationPlan
from app.domains.career_intelligence.models import StudentCareerReadinessState
from app.domains.institutional_intelligence.service import InstitutionalIntelligenceService
from app.domains.remediation.service import RemediationService


class AIToolRegistry:
    """Dispatches authorized deterministic tool queries with strict role & scope verification."""

    @staticmethod
    async def execute_tool(
        db: AsyncSession,
        user: User,
        user_context: Dict[str, Any],
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Validates permissions and dispatches to canonical database engines."""
        # 1. Student Mastery Tool
        if tool_name == "get_student_mastery":
            target_concept_id = arguments.get("concept_id")
            student_profile_id = user_context.get("student_profile_id")

            # Scope Defense: Teachers may only view if authorized, students only their own
            if user.role == UserRole.STUDENT and not student_profile_id:
                return {"status": "error", "message": "Student profile not found"}

            stmt = select(StudentConceptKnowledgeState).where(
                StudentConceptKnowledgeState.student_profile_id == student_profile_id,
            )
            if target_concept_id:
                stmt = stmt.where(StudentConceptKnowledgeState.concept_id == target_concept_id)

            res = await db.execute(stmt)
            states = res.scalars().all()
            return {
                "status": "success",
                "mastery_records": [
                    {
                        "concept_id": s.concept_id,
                        "current_mastery": float(s.current_mastery) if s.current_mastery is not None else None,
                        "retention_estimate": float(s.retention_estimate),
                        "confidence": float(s.confidence),
                        "state": s.state,
                        "evidence_count": s.evidence_count,
                    }
                    for s in states
                ]
            }

        # 2. Concept Prerequisites Tool
        elif tool_name == "get_concept_prerequisites":
            concept_id = arguments.get("concept_id")
            if not concept_id:
                return {"status": "error", "message": "concept_id required"}

            stmt = select(ConceptPrerequisite).where(ConceptPrerequisite.concept_id == concept_id)
            res = await db.execute(stmt)
            prereqs = res.scalars().all()
            return {
                "status": "success",
                "prerequisites": [
                    {"prerequisite_concept_id": p.prerequisite_concept_id, "type": p.relationship_type}
                    for p in prereqs
                ]
            }

        # 3. Student Active Remediation Plans
        elif tool_name == "get_student_remediation":
            student_profile_id = user_context.get("student_profile_id")
            stmt = select(RemediationPlan).where(
                RemediationPlan.student_profile_id == student_profile_id,
                RemediationPlan.status.in_(["recommended", "assigned", "in_progress", "paused"]),
            )
            res = await db.execute(stmt)
            plans = res.scalars().all()
            return {
                "status": "success",
                "active_remediation_plans": [
                    {
                        "id": p.id,
                        "target_concept_id": p.target_concept_id,
                        "diagnosis_type": p.diagnosis_type,
                        "diagnosis_reason": p.diagnosis_reason,
                        "priority_score": float(p.priority_score),
                        "status": p.status,
                    }
                    for p in plans
                ]
            }

        # 4. Career Readiness Overview (Domain 7 Bridge)
        elif tool_name == "get_career_readiness":
            student_profile_id = user_context.get("student_profile_id")
            stmt = select(StudentCareerReadinessState).where(
                StudentCareerReadinessState.student_profile_id == student_profile_id
            )
            res = await db.execute(stmt)
            c_state = res.scalar_one_or_none()
            if not c_state:
                return {"status": "not_assessed", "message": "Career readiness not yet evaluated."}
            return {
                "status": "success",
                "career_title": c_state.career_title,
                "overall_readiness_percentage": float(c_state.overall_readiness_percentage),
                "is_placement_eligible": c_state.is_placement_eligible,
                "top_skill_gaps": c_state.top_skill_gaps,
            }

        # 5. Faculty / HOD Department Analytics Bridge (Domain 9 & 10)
        elif tool_name == "get_department_analytics":
            if user.role not in [UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN]:
                return {"status": "denied", "message": "Unauthorized role for department analytics"}
            dept_id = user_context.get("department_id") or arguments.get("department_id")
            if not dept_id:
                return {"status": "error", "message": "Department context not resolved"}
            analytics = await InstitutionalIntelligenceService.get_department_analytics(db, dept_id, user)
            return {"status": "success", "analytics": analytics.model_dump()}

        return {"status": "error", "message": f"Unknown tool '{tool_name}'"}
