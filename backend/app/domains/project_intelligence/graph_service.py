"""Skill Graph and Evidence Graph Service for Domain 8.

Answers: 'Why does Dhruva think this student has this skill?'
Connects Career -> Skills -> Concepts -> Courses -> Assessments -> Projects -> Evidence -> Portfolio -> Career Readiness.
Executes deterministic, relational graph traversals over PostgreSQL without needing an external graph DB.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.domains.catalog.models import (
    SkillCatalog,
    CareerCatalog,
    CareerSkillMapping,
    CourseCatalog,
    CourseSkillMapping,
)
from app.domains.content.models import (
    Concept,
    ConceptSkill,
    CourseSkill,
    LessonSkill,
)
from app.domains.assessment.models import SkillEvidence
from app.domains.mastery.models import StudentConceptKnowledgeState
from app.domains.profiles.models import (
    StudentSkill,
    StudentProject,
    StudentProjectSkill,
    StudentCareerGoal,
)
from app.domains.career_intelligence.models import (
    StudentSkillIntelligenceState,
    StudentSkillEvidenceRecord,
)
from app.domains.project_intelligence.models import (
    ProjectConcept,
    ProjectEvidence,
    ProjectReview,
)


class SkillGraphService:
    """Relational traversals answering multi-dimensional skill and evidence queries."""

    async def get_skill_evidence_graph(
        self,
        db: AsyncSession,
        skill_id: str,
        student_profile_id: str,
    ) -> Dict[str, Any]:
        """Constructs an auditable evidence graph for a specific skill and student."""
        # 1. Skill metadata
        skill = await db.get(SkillCatalog, skill_id)
        if not skill:
            return {"error": "Skill not found in catalog"}

        # 2. Authoritative Skill Intelligence State from Domain 7
        st_stmt = select(StudentSkillIntelligenceState).where(
            and_(
                StudentSkillIntelligenceState.student_profile_id == student_profile_id,
                StudentSkillIntelligenceState.skill_id == skill_id,
            )
        )
        skill_state = (await db.execute(st_stmt)).scalar_one_or_none()

        # 3. Supporting Concepts via ConceptSkill
        cs_stmt = (
            select(ConceptSkill, Concept)
            .join(Concept, ConceptSkill.concept_id == Concept.id)
            .where(ConceptSkill.skill_id == skill_id)
        )
        cs_rows = (await db.execute(cs_stmt)).all()
        concept_ids = [c.id for _, c in cs_rows]

        # Student's mastery on these concepts from Domain 6
        concept_masteries: Dict[str, Any] = {}
        if concept_ids:
            ks_stmt = select(StudentConceptKnowledgeState).where(
                and_(
                    StudentConceptKnowledgeState.student_profile_id == student_profile_id,
                    StudentConceptKnowledgeState.concept_id.in_(concept_ids),
                )
            )
            for ks in (await db.execute(ks_stmt)).scalars().all():
                concept_masteries[ks.concept_id] = {
                    "mastery": float(ks.current_mastery) if ks.current_mastery is not None else 0.0,
                    "confidence": float(ks.confidence_score) if ks.confidence_score is not None else 0.0,
                    "retention": float(ks.retention_estimate) if ks.retention_estimate is not None else 0.0,
                    "classification": ks.state_classification,
                }

        supporting_concepts = []
        for cs, c in cs_rows:
            m_data = concept_masteries.get(c.id, {})
            supporting_concepts.append({
                "concept_id": c.id,
                "concept_name": c.name,
                "weight": float(cs.weight),
                "is_core": cs.is_core,
                "mastery": m_data.get("mastery", 0.0),
                "classification": m_data.get("classification", "unknown"),
            })

        # 4. Connected Courses via CourseSkillMapping
        course_stmt = (
            select(CourseSkillMapping, CourseCatalog)
            .join(CourseCatalog, CourseSkillMapping.course_catalog_id == CourseCatalog.id)
            .where(CourseSkillMapping.skill_id == skill_id)
        )
        courses = []
        for cs, crs in (await db.execute(course_stmt)).all():
            courses.append({
                "course_id": crs.id,
                "course_code": crs.code,
                "course_title": crs.title,
                "weight": float(cs.weight),
            })

        # 5. Connected Assessment Evidence from Domain 5
        asst_stmt = select(SkillEvidence).where(
            and_(
                SkillEvidence.student_profile_id == student_profile_id,
                SkillEvidence.skill_id == skill_id,
            )
        )
        assessment_ev_rows = (await db.execute(asst_stmt)).scalars().all()
        assessment_ev_items = [
            {
                "evidence_id": ev.id,
                "score": float(ev.score),
                "weight": float(ev.weight) if ev.weight else 1.0,
                "evidence_type": ev.evidence_type,
                "recorded_at": ev.recorded_at.isoformat() if ev.recorded_at else None,
            }
            for ev in assessment_ev_rows
        ]

        # 6. Connected Projects from Domain 8
        proj_stmt = (
            select(StudentProjectSkill, StudentProject)
            .join(StudentProject, StudentProjectSkill.project_id == StudentProject.id)
            .where(
                and_(
                    StudentProject.student_profile_id == student_profile_id,
                    StudentProjectSkill.skill_catalog_id == skill_id,
                )
            )
        )
        project_rows = (await db.execute(proj_stmt)).all()
        projects_demonstrated = []
        for ps, p in project_rows:
            projects_demonstrated.append({
                "project_id": p.id,
                "title": p.title,
                "project_type": p.project_type,
                "status": p.status,
                "is_verified": p.is_verified,
                "claimed_level": ps.claimed_level,
                "evidence_strength": ps.evidence_strength,
                "verification_status": ps.verification_status,
                "quality_score": p.quality_score,
            })

        # 7. Connected Project Evidence Items
        project_ids = [p.id for _, p in project_rows]
        project_ev_items = []
        if project_ids:
            pev_stmt = select(ProjectEvidence).where(
                and_(
                    ProjectEvidence.project_id.in_(project_ids),
                    ProjectEvidence.student_profile_id == student_profile_id,
                )
            )
            for pev in (await db.execute(pev_stmt)).scalars().all():
                project_ev_items.append({
                    "id": pev.id,
                    "project_id": pev.project_id,
                    "evidence_type": pev.evidence_type,
                    "title": pev.title,
                    "source": pev.source,
                    "source_reference": pev.source_reference,
                    "verification_status": pev.verification_status,
                    "evidence_strength": pev.evidence_strength,
                })

        # 8. Career Context: which careers require this skill?
        car_stmt = (
            select(CareerSkillMapping, CareerCatalog)
            .join(CareerCatalog, CareerSkillMapping.career_id == CareerCatalog.id)
            .where(CareerSkillMapping.skill_id == skill_id)
        )
        careers_requiring = []
        for csm, car in (await db.execute(car_stmt)).all():
            careers_requiring.append({
                "career_id": car.id,
                "career_title": car.title,
                "importance": csm.importance,
                "weight": float(csm.weight),
            })

        # Synthesize explainability summary
        provenance_summary = {
            "assessments_count": len(assessment_ev_items),
            "mastered_concepts_count": sum(1 for c in supporting_concepts if c["mastery"] >= 0.8),
            "courses_count": len(courses),
            "projects_count": len(projects_demonstrated),
            "verified_projects_count": sum(1 for p in projects_demonstrated if p["is_verified"]),
            "project_evidence_items_count": len(project_ev_items),
        }

        return {
            "skill_id": skill.id,
            "skill_name": skill.name,
            "skill_code": skill.code,
            "category": skill.category,
            "state": {
                "observed_proficiency": float(skill_state.observed_proficiency) if skill_state else 0.0,
                "verified_proficiency": float(skill_state.verified_proficiency) if skill_state else 0.0,
                "confidence": float(skill_state.confidence) if skill_state else 0.0,
                "verification_status": skill_state.verification_status if skill_state else "unverified",
                "proficiency_tier": skill_state.proficiency_tier if skill_state else "exposure",
            },
            "provenance_summary": provenance_summary,
            "concepts": supporting_concepts,
            "courses": courses,
            "assessments": assessment_ev_items,
            "projects": projects_demonstrated,
            "project_evidence": project_ev_items,
            "target_careers": careers_requiring,
        }

    async def get_student_skill_graph(
        self,
        db: AsyncSession,
        student_profile_id: str,
    ) -> Dict[str, Any]:
        """Returns the full multi-dimensional skill graph for a student."""
        # 1. Fetch all evaluated skills for the student
        st_stmt = (
            select(StudentSkillIntelligenceState, SkillCatalog)
            .join(SkillCatalog, StudentSkillIntelligenceState.skill_id == SkillCatalog.id)
            .where(StudentSkillIntelligenceState.student_profile_id == student_profile_id)
        )
        evaluated_skills = (await db.execute(st_stmt)).all()

        # 2. Fetch student's target career goals
        cg_stmt = (
            select(StudentCareerGoal, CareerCatalog)
            .join(CareerCatalog, StudentCareerGoal.career_catalog_id == CareerCatalog.id)
            .where(StudentCareerGoal.student_profile_id == student_profile_id)
            .order_by(StudentCareerGoal.priority.asc())
        )
        career_goals = (await db.execute(cg_stmt)).all()
        primary_career = career_goals[0][1] if career_goals else None

        # 3. If primary career exists, load requirements
        career_reqs: Dict[str, Any] = {}
        if primary_career:
            csm_stmt = select(CareerSkillMapping).where(CareerSkillMapping.career_id == primary_career.id)
            for csm in (await db.execute(csm_stmt)).scalars().all():
                career_reqs[csm.skill_id] = {
                    "importance": csm.importance,
                    "weight": float(csm.weight),
                }

        # 4. Fetch all projects and project skills
        proj_stmt = (
            select(StudentProject)
            .options(
                selectinload(StudentProject.project_skills).selectinload(StudentProjectSkill.skill_catalog),
                selectinload(StudentProject.evidence_items),
                selectinload(StudentProject.reviews),
            )
            .where(StudentProject.student_profile_id == student_profile_id)
        )
        projects = (await db.execute(proj_stmt)).scalars().all()

        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []

        # Add Career Node if present
        if primary_career:
            nodes.append({
                "id": f"career_{primary_career.id}",
                "type": "career",
                "label": primary_career.title,
                "data": {"code": primary_career.code, "industry": primary_career.industry},
            })

        # Add Skill Nodes
        for st, skl in evaluated_skills:
            req_info = career_reqs.get(skl.id)
            is_gap = req_info is not None and float(st.verified_proficiency) < 0.60

            node_id = f"skill_{skl.id}"
            nodes.append({
                "id": node_id,
                "type": "skill",
                "label": skl.name,
                "data": {
                    "code": skl.code,
                    "proficiency": float(st.verified_proficiency),
                    "confidence": float(st.confidence),
                    "tier": st.proficiency_tier,
                    "status": st.verification_status,
                    "is_career_required": req_info is not None,
                    "importance": req_info["importance"] if req_info else None,
                    "is_gap": is_gap,
                },
            })

            # Edge from career to skill
            if primary_career and req_info:
                edges.append({
                    "id": f"edge_career_{primary_career.id}_to_skill_{skl.id}",
                    "source": f"career_{primary_career.id}",
                    "target": node_id,
                    "type": "requires_skill",
                    "label": req_info["importance"],
                })

        # Add Project Nodes
        for p in projects:
            p_node_id = f"project_{p.id}"
            nodes.append({
                "id": p_node_id,
                "type": "project",
                "label": p.title,
                "data": {
                    "type": p.project_type,
                    "status": p.status,
                    "is_verified": p.is_verified,
                    "quality_score": p.quality_score,
                    "evidence_count": len(p.evidence_items),
                },
            })

            # Edges from project to demonstrated skills
            for ps in p.project_skills:
                edges.append({
                    "id": f"edge_project_{p.id}_to_skill_{ps.skill_catalog_id}",
                    "source": p_node_id,
                    "target": f"skill_{ps.skill_catalog_id}",
                    "type": "demonstrates_skill",
                    "label": ps.claimed_level,
                    "is_verified": ps.verification_status == "verified",
                })

        return {
            "student_profile_id": student_profile_id,
            "target_career": {
                "id": primary_career.id,
                "title": primary_career.title,
            } if primary_career else None,
            "nodes_count": len(nodes),
            "edges_count": len(edges),
            "nodes": nodes,
            "edges": edges,
        }


skill_graph_service = SkillGraphService()
