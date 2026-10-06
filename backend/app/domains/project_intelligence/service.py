"""Transactional service for Domain 8: Project Intelligence, Evidence Graph & Portfolio Engine."""

import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.domains.identity.models import User
from app.domains.academic.models import StudentAcademicProfile
from app.domains.catalog.models import (
    SkillCatalog,
    CareerCatalog,
    CareerSkillMapping,
)
from app.domains.content.models import Concept
from app.domains.profiles.models import (
    StudentProject,
    StudentProjectSkill,
    StudentPortfolio,
    StudentSkill,
    StudentCareerGoal,
    StudentCertification,
    StudentAchievement,
)
from app.domains.project_intelligence.models import (
    ProjectConcept,
    ProjectEvidence,
    ProjectReview,
    PortfolioIntelligenceSnapshot,
)
from app.domains.project_intelligence.quality_engine import (
    ProjectQualityEngine,
    ProjectQualityInput,
    ProjectQualityResult,
)
from app.domains.project_intelligence.relevance_engine import (
    CareerRelevanceEngine,
    CareerSkillRequirementItem,
    CareerRelevanceResult,
)
from app.domains.project_intelligence.portfolio_engine import (
    PortfolioIntelligenceEngine,
    PortfolioEvaluationInput,
    ProjectSummaryItem,
    PortfolioHealthResult,
)
from app.domains.project_intelligence.providers import repository_provider
from app.domains.career_intelligence.service import career_intelligence_service
from app.domains.career_intelligence.models import StudentSkillEvidenceRecord


class ProjectIntelligenceService:
    """Manages project lifecycles, empirical evidence ingestion, rubric evaluations, and portfolio health."""

    def __init__(self):
        self.quality_engine = ProjectQualityEngine()
        self.relevance_engine = CareerRelevanceEngine()
        self.portfolio_engine = PortfolioIntelligenceEngine()

    @staticmethod
    def slugify(text: str) -> str:
        s = text.lower().strip()
        s = re.sub(r"[^\w\s-]", "", s)
        s = re.sub(r"[\s_-]+", "-", s)
        return s.strip("-")

    # =========================================================================
    # 1. Project Management
    # =========================================================================

    async def create_project(
        self,
        db: AsyncSession,
        student_profile_id: str,
        data: Dict[str, Any],
    ) -> StudentProject:
        """Creates a new student project and maps initial skills/concepts."""
        now = datetime.now(timezone.utc)
        title = data["title"]
        slug = data.get("slug") or f"{self.slugify(title)}-{uuid_tail()}"

        project = StudentProject(
            student_profile_id=student_profile_id,
            title=title,
            slug=slug,
            description=data.get("description"),
            short_description=data.get("short_description"),
            problem_statement=data.get("problem_statement"),
            solution=data.get("solution"),
            project_type=data.get("project_type", "academic"),
            status=data.get("status", "in_progress"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            repository_url=data.get("repository_url"),
            live_url=data.get("live_url"),
            demo_url=data.get("demo_url"),
            documentation_url=data.get("documentation_url"),
            technologies=data.get("technologies") or [],
            team_or_individual=data.get("team_or_individual", "individual"),
            role=data.get("role"),
            team_size=data.get("team_size", 1),
            contribution_description=data.get("contribution_description"),
            contribution_percentage=data.get("contribution_percentage"),
            modules_contributed=data.get("modules_contributed") or [],
            visibility=data.get("visibility", "private"),
            verification_status="unverified",
            is_verified=False,
            created_at=now,
            updated_at=now,
        )
        db.add(project)
        await db.flush()

        # Map skills
        skill_ids = data.get("skill_ids") or []
        for sid in skill_ids:
            ps = StudentProjectSkill(
                project_id=project.id,
                skill_catalog_id=sid,
                claimed_level="intermediate",
                evidence_strength=0.5,
                verification_status="unverified",
                source="student_claim",
                created_at=now,
            )
            db.add(ps)

        # Map concepts
        concept_ids = data.get("concept_ids") or []
        for cid in concept_ids:
            pc = ProjectConcept(
                project_id=project.id,
                concept_id=cid,
                demonstrated_level="proficient",
                verification_status="unverified",
                created_at=now,
            )
            db.add(pc)

        # Ingest repository metadata if URL provided
        if project.repository_url:
            meta = repository_provider.parse_repository_url(project.repository_url)
            if meta:
                ev = ProjectEvidence(
                    project_id=project.id,
                    student_profile_id=student_profile_id,
                    evidence_type="repository",
                    source=meta.provider,
                    source_reference=meta.normalized_url,
                    title=f"Source Repository ({meta.repo_name})",
                    description=f"Public source code repository hosted on {meta.provider.capitalize()}.",
                    submitted_at=now,
                    verification_status="submitted",
                    evidence_strength=0.75,
                    metadata_json=meta.metadata_details,
                )
                db.add(ev)

        await db.flush()
        # Evaluate initial quality & career relevance
        await self.recalculate_project_intelligence(db, project.id)
        return project

    async def update_project(
        self,
        db: AsyncSession,
        project_id: str,
        student_profile_id: str,
        data: Dict[str, Any],
    ) -> StudentProject:
        """Updates project metadata and refreshes quality evaluations."""
        project = await db.get(StudentProject, project_id)
        if not project or project.student_profile_id != student_profile_id:
            raise ValueError("Project not found or unauthorized.")

        now = datetime.now(timezone.utc)
        for field, val in data.items():
            if val is not None and hasattr(project, field) and field not in ["id", "student_profile_id", "created_at"]:
                setattr(project, field, val)

        project.updated_at = now
        await db.flush()

        if "skill_ids" in data and data["skill_ids"] is not None:
            # Refresh skills
            existing = (await db.execute(select(StudentProjectSkill).where(StudentProjectSkill.project_id == project.id))).scalars().all()
            for ex in existing:
                await db.delete(ex)
            for sid in data["skill_ids"]:
                ps = StudentProjectSkill(
                    project_id=project.id,
                    skill_catalog_id=sid,
                    claimed_level="intermediate",
                    evidence_strength=0.5,
                    verification_status="unverified",
                    source="student_claim",
                    created_at=now,
                )
                db.add(ps)
            await db.flush()

        await self.recalculate_project_intelligence(db, project.id)
        return project

    async def get_project_with_details(
        self,
        db: AsyncSession,
        project_id: str,
    ) -> Optional[StudentProject]:
        """Loads a project with complete skills, concepts, evidence, and reviews."""
        stmt = (
            select(StudentProject)
            .options(
                selectinload(StudentProject.project_skills).selectinload(StudentProjectSkill.skill_catalog),
                selectinload(StudentProject.project_concepts).selectinload(ProjectConcept.concept),
                selectinload(StudentProject.evidence_items),
                selectinload(StudentProject.reviews).selectinload(ProjectReview.reviewer),
            )
            .where(StudentProject.id == project_id)
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    async def delete_project(
        self,
        db: AsyncSession,
        project_id: str,
        student_profile_id: str,
    ) -> None:
        """Deletes a student project and cascades associated records."""
        project = await db.get(StudentProject, project_id)
        if not project or project.student_profile_id != student_profile_id:
            raise ValueError("Project not found or unauthorized.")
        await db.delete(project)
        await db.flush()

    # =========================================================================
    # 2. Evidence Submission & Verification
    # =========================================================================

    async def add_project_evidence(
        self,
        db: AsyncSession,
        project_id: str,
        student_profile_id: str,
        evidence_in: Dict[str, Any],
    ) -> ProjectEvidence:
        """Student submits a new empirical evidence item for a project."""
        project = await db.get(StudentProject, project_id)
        if not project or project.student_profile_id != student_profile_id:
            raise ValueError("Project not found or unauthorized.")

        now = datetime.now(timezone.utc)
        ev = ProjectEvidence(
            project_id=project_id,
            student_profile_id=student_profile_id,
            evidence_type=evidence_in["evidence_type"],
            source=evidence_in.get("source", "github"),
            source_reference=evidence_in["source_reference"],
            title=evidence_in["title"],
            description=evidence_in.get("description"),
            submitted_at=now,
            verification_status="submitted",
            evidence_strength=evidence_in.get("evidence_strength", 0.80),
            metadata_json=evidence_in.get("metadata_json"),
        )
        db.add(ev)
        await db.flush()

        await self.recalculate_project_intelligence(db, project_id)
        return ev

    async def verify_project_evidence(
        self,
        db: AsyncSession,
        evidence_id: str,
        reviewer_user: User,
        decision: str,  # verified, rejected
        verification_notes: Optional[str] = None,
    ) -> ProjectEvidence:
        """Authorized reviewer verifies or rejects an evidence record."""
        ev = await db.get(ProjectEvidence, evidence_id)
        if not ev:
            raise ValueError("Evidence item not found.")

        # Invariant: Student cannot self-verify evidence
        student_prof = await db.get(StudentAcademicProfile, ev.student_profile_id)
        if student_prof and student_prof.user_id == reviewer_user.id:
            raise PermissionError("Students cannot verify their own evidence.")

        now = datetime.now(timezone.utc)
        ev.verification_status = "verified" if decision == "verified" else "rejected"
        ev.verified_by_user_id = reviewer_user.id
        ev.verified_at = now
        if verification_notes:
            meta = ev.metadata_json or {}
            meta["verification_notes"] = verification_notes
            ev.metadata_json = meta

        await db.flush()
        await self.recalculate_project_intelligence(db, ev.project_id)

        # Feed verified evidence into Domain 7 skill intelligence
        if decision == "verified":
            await self._feed_verified_project_into_skill_intelligence(db, ev.project_id, ev.student_profile_id)

        return ev

    # =========================================================================
    # 3. Faculty Project Review Workflow
    # =========================================================================

    async def submit_faculty_review(
        self,
        db: AsyncSession,
        project_id: str,
        reviewer_user: User,
        review_data: Dict[str, Any],
    ) -> ProjectReview:
        """Submits structured rubric evaluation by faculty/mentor and updates project status."""
        project = await db.get(StudentProject, project_id)
        if not project:
            raise ValueError("Project not found.")

        # Invariant: Self-review prohibited
        student_prof = await db.get(StudentAcademicProfile, project.student_profile_id)
        if student_prof and student_prof.user_id == reviewer_user.id:
            raise PermissionError("Students cannot review their own project.")

        # Compute deterministic overall score from 10 rubric dimensions
        dim_names = [
            "technical_depth", "problem_solving", "code_quality", "architecture_quality",
            "documentation_quality", "testing_quality", "practical_application",
            "originality", "student_contribution_score", "professional_presentation"
        ]
        scores = [float(review_data.get(k, 70.0)) for k in dim_names]
        overall_score = round(sum(scores) / len(scores), 2)

        now = datetime.now(timezone.utc)
        review = ProjectReview(
            project_id=project_id,
            reviewer_user_id=reviewer_user.id,
            review_type=review_data.get("review_type", "faculty"),
            technical_depth=float(review_data.get("technical_depth", 70.0)),
            problem_solving=float(review_data.get("problem_solving", 70.0)),
            code_quality=float(review_data.get("code_quality", 70.0)),
            architecture_quality=float(review_data.get("architecture_quality", 70.0)),
            documentation_quality=float(review_data.get("documentation_quality", 70.0)),
            testing_quality=float(review_data.get("testing_quality", 70.0)),
            practical_application=float(review_data.get("practical_application", 70.0)),
            originality=float(review_data.get("originality", 70.0)),
            student_contribution_score=float(review_data.get("student_contribution_score", 70.0)),
            professional_presentation=float(review_data.get("professional_presentation", 70.0)),
            overall_score=overall_score,
            rubric_breakdown={k: float(review_data.get(k, 70.0)) for k in dim_names},
            feedback=review_data.get("feedback"),
            decision=review_data.get("decision", "approved"),
            is_finalized=True,
            reviewed_at=now,
        )
        db.add(review)

        # Update Project verification status based on review decision
        if review.decision == "approved":
            project.is_verified = True
            project.verification_status = "verified"
            project.verified_by_user_id = reviewer_user.id

            # Also mark all project skills as verified
            ps_stmt = select(StudentProjectSkill).where(StudentProjectSkill.project_id == project_id)
            for ps in (await db.execute(ps_stmt)).scalars().all():
                ps.verification_status = "verified"
                ps.verified_by_user_id = reviewer_user.id
                ps.verified_at = now
        elif review.decision == "rejected":
            project.verification_status = "rejected"
        else:
            project.verification_status = "under_review"

        await db.flush()
        await self.recalculate_project_intelligence(db, project_id)

        # Feed verified project evidence to Domain 7
        if review.decision == "approved":
            await self._feed_verified_project_into_skill_intelligence(db, project.id, project.student_profile_id)

        return review

    # =========================================================================
    # 4. Intelligence Recalculation & Domain 7 Bridge
    # =========================================================================

    async def recalculate_project_intelligence(
        self,
        db: AsyncSession,
        project_id: str,
    ) -> Tuple[ProjectQualityResult, Optional[CareerRelevanceResult]]:
        """Executes pure deterministic evaluation of quality and career relevance."""
        project = await self.get_project_with_details(db, project_id)
        if not project:
            raise ValueError("Project not found.")

        # Check evidence for tests and architecture
        has_tests = any("test" in ev.evidence_type.lower() for ev in project.evidence_items)
        has_arch = any("architecture" in ev.evidence_type.lower() or "diagram" in ev.evidence_type.lower() for ev in project.evidence_items)

        # Latest faculty review breakdown if available
        latest_review = project.reviews[-1] if project.reviews else None
        rev_score = latest_review.overall_score if latest_review else None
        rev_breakdown = latest_review.rubric_breakdown if latest_review else None

        q_input = ProjectQualityInput(
            title=project.title,
            description=project.description,
            problem_statement=project.problem_statement,
            solution=project.solution,
            technologies=project.technologies or [],
            status=project.status,
            repository_url=project.repository_url,
            live_url=project.live_url,
            documentation_url=project.documentation_url,
            demo_url=project.demo_url,
            modules_contributed=project.modules_contributed or [],
            skills_count=len(project.project_skills),
            concepts_count=len(project.project_concepts),
            evidence_items_count=len(project.evidence_items),
            verified_evidence_count=sum(1 for ev in project.evidence_items if ev.verification_status == "verified"),
            has_test_evidence=has_tests,
            has_architecture_diagram=has_arch,
            faculty_review_score=rev_score,
            faculty_review_breakdown=rev_breakdown,
            is_verified=project.is_verified,
        )
        q_res = self.quality_engine.evaluate_project(q_input)
        project.quality_score = q_res.overall_score
        project.quality_breakdown = q_res.dimension_breakdown

        # Career Relevance against student's primary career goal
        cg_stmt = (
            select(StudentCareerGoal, CareerCatalog)
            .join(CareerCatalog, StudentCareerGoal.career_catalog_id == CareerCatalog.id)
            .where(StudentCareerGoal.student_profile_id == project.student_profile_id)
            .order_by(StudentCareerGoal.priority.asc())
        )
        cg_row = (await db.execute(cg_stmt)).first()

        rel_res: Optional[CareerRelevanceResult] = None
        if cg_row:
            career = cg_row[1]
            csm_stmt = (
                select(CareerSkillMapping, SkillCatalog)
                .join(SkillCatalog, CareerSkillMapping.skill_id == SkillCatalog.id)
                .where(CareerSkillMapping.career_id == career.id)
            )
            csm_rows = (await db.execute(csm_stmt)).all()
            req_items = [
                CareerSkillRequirementItem(
                    skill_id=m.skill_id,
                    skill_name=skl.name,
                    importance=m.importance,
                    weight=float(m.weight),
                )
                for m, skl in csm_rows
            ]

            p_skill_ids = [ps.skill_catalog_id for ps in project.project_skills]
            p_skill_names = {
                ps.skill_catalog_id: ps.skill_catalog.name if ps.skill_catalog else ps.skill_catalog_id
                for ps in project.project_skills
            }

            rel_res = self.relevance_engine.evaluate_relevance(
                project_id=project.id,
                project_title=project.title,
                project_skill_ids=p_skill_ids,
                project_skill_names=p_skill_names,
                career_id=career.id,
                career_title=career.title,
                career_requirements=req_items,
            )
            project.career_relevance_score = rel_res.relevance_score
            project.career_relevance_category = rel_res.relevance_tier

        await db.flush()
        return q_res, rel_res

    async def _feed_verified_project_into_skill_intelligence(
        self,
        db: AsyncSession,
        project_id: str,
        student_profile_id: str,
    ) -> None:
        """Bridges Domain 8 to Domain 7: writes verified practical evidence into skill intelligence states."""
        project = await self.get_project_with_details(db, project_id)
        if not project:
            return

        now = datetime.now(timezone.utc)
        score = Decimal(str(round((project.quality_score or 75.0) / 100.0, 4)))

        for ps in project.project_skills:
            # Check if an evidence record already exists for this project + skill
            existing_ev = await db.execute(
                select(StudentSkillEvidenceRecord).where(
                    and_(
                        StudentSkillEvidenceRecord.student_profile_id == student_profile_id,
                        StudentSkillEvidenceRecord.skill_id == ps.skill_catalog_id,
                        StudentSkillEvidenceRecord.source_id == project.id,
                    )
                )
            )
            ev_rec = existing_ev.scalar_one_or_none()
            if not ev_rec:
                ev_rec = StudentSkillEvidenceRecord(
                    student_profile_id=student_profile_id,
                    skill_id=ps.skill_catalog_id,
                    source_type="project",
                    source_id=project.id,
                    evidence_score=score,
                    evidence_weight=Decimal("0.9000"),
                    is_verified=True,
                    provenance_details={"project_title": project.title, "quality_score": project.quality_score},
                    recorded_at=now,
                )
                db.add(ev_rec)
            else:
                ev_rec.evidence_score = score
                ev_rec.is_verified = True

        await db.flush()
        # Trigger Domain 7 recomputation of verified skill tiers and readiness
        await career_intelligence_service.evaluate_all_student_skills(db, student_profile_id)

    # =========================================================================
    # 5. Portfolio Intelligence & Builder
    # =========================================================================

    async def get_or_create_portfolio(
        self,
        db: AsyncSession,
        student_profile_id: str,
    ) -> StudentPortfolio:
        """Retrieves or provisions student portfolio record."""
        stmt = select(StudentPortfolio).where(StudentPortfolio.student_profile_id == student_profile_id)
        port = (await db.execute(stmt)).scalar_one_or_none()
        if not port:
            now = datetime.now(timezone.utc)
            port = StudentPortfolio(
                student_profile_id=student_profile_id,
                theme="modern",
                public_visibility=False,
                created_at=now,
                updated_at=now,
            )
            db.add(port)
            await db.flush()
        return port

    async def update_portfolio(
        self,
        db: AsyncSession,
        student_profile_id: str,
        data: Dict[str, Any],
    ) -> StudentPortfolio:
        """Updates portfolio customization."""
        port = await self.get_or_create_portfolio(db, student_profile_id)
        now = datetime.now(timezone.utc)
        for field, val in data.items():
            if val is not None and hasattr(port, field) and field not in ["id", "student_profile_id", "created_at"]:
                setattr(port, field, val)
        port.updated_at = now
        await db.flush()
        return port

    async def evaluate_portfolio_health(
        self,
        db: AsyncSession,
        student_profile_id: str,
    ) -> PortfolioHealthResult:
        """Deterministic evaluation of portfolio health, diversity, depth, and completeness."""
        port = await self.get_or_create_portfolio(db, student_profile_id)

        # Load projects
        proj_stmt = (
            select(StudentProject)
            .options(selectinload(StudentProject.evidence_items))
            .where(StudentProject.student_profile_id == student_profile_id)
        )
        projects = (await db.execute(proj_stmt)).scalars().all()

        # Check career goal
        cg_stmt = select(StudentCareerGoal).where(StudentCareerGoal.student_profile_id == student_profile_id)
        has_goal = bool((await db.execute(cg_stmt)).first())

        # Load skills count
        sk_stmt = select(func.count(StudentSkill.id)).where(StudentSkill.student_profile_id == student_profile_id)
        total_skills = (await db.execute(sk_stmt)).scalar() or 0

        vsk_stmt = select(func.count(StudentSkill.id)).where(
            and_(StudentSkill.student_profile_id == student_profile_id, StudentSkill.is_verified == True)
        )
        verified_skills = (await db.execute(vsk_stmt)).scalar() or 0

        # Load certifications
        cert_stmt = select(func.count(StudentCertification.id)).where(StudentCertification.student_profile_id == student_profile_id)
        total_certs = (await db.execute(cert_stmt)).scalar() or 0

        vcert_stmt = select(func.count(StudentCertification.id)).where(
            and_(StudentCertification.student_profile_id == student_profile_id, StudentCertification.status == "verified")
        )
        verified_certs = (await db.execute(vcert_stmt)).scalar() or 0

        # Load achievements
        ach_stmt = select(func.count(StudentAchievement.id)).where(StudentAchievement.student_profile_id == student_profile_id)
        total_ach = (await db.execute(ach_stmt)).scalar() or 0

        p_items: List[ProjectSummaryItem] = []
        for p in projects:
            has_prob_sol = bool(p.problem_statement and p.solution)
            has_repo_demo = bool(p.repository_url or p.live_url or p.demo_url)
            is_aligned = (p.career_relevance_category in ["high", "medium"]) if p.career_relevance_category else False

            p_items.append(ProjectSummaryItem(
                id=p.id,
                title=p.title,
                project_type=p.project_type,
                status=p.status,
                is_verified=p.is_verified,
                quality_score=p.quality_score,
                has_problem_and_solution=has_prob_sol,
                has_repo_or_demo=has_repo_demo,
                skills_count=0,
                evidence_count=len(p.evidence_items),
                is_career_aligned=is_aligned,
            ))

        port_in = PortfolioEvaluationInput(
            has_portfolio_record=True,
            headline=port.headline,
            bio=port.bio,
            contact_email=port.contact_email,
            social_links_count=len(port.social_links) if port.social_links else 0,
            custom_links_count=len(port.custom_links) if port.custom_links else 0,
            public_visibility=port.public_visibility,
            projects=p_items,
            total_skills_count=total_skills,
            verified_skills_count=verified_skills,
            total_certifications_count=total_certs,
            verified_certifications_count=verified_certs,
            total_achievements_count=total_ach,
            has_career_goal=has_goal,
        )

        h_res = self.portfolio_engine.evaluate_portfolio(port_in)

        # Upsert snapshot
        now = datetime.now(timezone.utc)
        snap_stmt = select(PortfolioIntelligenceSnapshot).where(
            PortfolioIntelligenceSnapshot.student_profile_id == student_profile_id
        )
        snap = (await db.execute(snap_stmt)).scalar_one_or_none()
        if not snap:
            snap = PortfolioIntelligenceSnapshot(student_profile_id=student_profile_id)
            db.add(snap)

        snap.overall_health_score = h_res.overall_health_score
        snap.status = h_res.status
        snap.technical_depth = h_res.technical_depth
        snap.project_diversity = h_res.project_diversity
        snap.evidence_quality = h_res.evidence_quality
        snap.documentation_quality = h_res.documentation_quality
        snap.career_alignment = h_res.career_alignment
        snap.professional_presence = h_res.professional_presence
        snap.verification_coverage = h_res.verification_coverage
        snap.completeness_score = h_res.completeness_score
        snap.missing_sections = h_res.missing_sections
        snap.dimension_explanations = h_res.dimension_explanations
        snap.algorithm_version = h_res.algorithm_version
        snap.evaluated_at = now

        await db.flush()
        return h_res

    async def get_public_portfolio(
        self,
        db: AsyncSession,
        slug_or_username: str,
    ) -> Optional[Dict[str, Any]]:
        """Retrieves safe public portfolio. Never leaks private notes, reviews, or unverified private records."""
        # Check by slug in StudentPortfolio
        p_stmt = (
            select(StudentPortfolio, StudentAcademicProfile, User)
            .join(StudentAcademicProfile, StudentPortfolio.student_profile_id == StudentAcademicProfile.id)
            .join(User, StudentAcademicProfile.user_id == User.id)
            .where(StudentPortfolio.slug == slug_or_username)
        )
        row = (await db.execute(p_stmt)).first()

        if not row:
            # Fallback check User normalized email or ID
            u_stmt = (
                select(StudentPortfolio, StudentAcademicProfile, User)
                .join(StudentAcademicProfile, StudentPortfolio.student_profile_id == StudentAcademicProfile.id)
                .join(User, StudentAcademicProfile.user_id == User.id)
                .where(
                    or_(
                        User.id == slug_or_username,
                        User.normalized_email == slug_or_username.lower(),
                    )
                )
            )
            row = (await db.execute(u_stmt)).first()

        if not row:
            return None

        port, prof, user = row
        # Must be explicitly public
        if not port.public_visibility:
            return None

        # Fetch only public / institution visible projects
        proj_stmt = (
            select(StudentProject)
            .options(selectinload(StudentProject.project_skills).selectinload(StudentProjectSkill.skill_catalog))
            .where(
                and_(
                    StudentProject.student_profile_id == prof.id,
                    StudentProject.visibility.in_(["public", "institution"]),
                )
            )
        )
        projects = (await db.execute(proj_stmt)).scalars().all()

        # Fetch verified skills
        sk_stmt = (
            select(StudentSkill, SkillCatalog)
            .join(SkillCatalog, StudentSkill.skill_catalog_id == SkillCatalog.id)
            .where(
                and_(
                    StudentSkill.student_profile_id == prof.id,
                    StudentSkill.is_verified == True,
                )
            )
        )
        skills = [
            {"name": skl.name, "proficiency": ss.proficiency, "category": skl.category}
            for ss, skl in (await db.execute(sk_stmt)).all()
        ]

        # Fetch verified certifications
        cert_stmt = select(StudentCertification).where(
            and_(StudentCertification.student_profile_id == prof.id, StudentCertification.status == "verified")
        )
        certs = [
            {"title": c.title, "issuer": c.issuer, "credential_url": c.credential_url, "issue_date": c.issue_date.isoformat() if c.issue_date else None}
            for c in (await db.execute(cert_stmt)).scalars().all()
        ]

        # Fetch verified achievements
        ach_stmt = select(StudentAchievement).where(
            and_(StudentAchievement.student_profile_id == prof.id, StudentAchievement.is_verified == True)
        )
        achievements = [
            {"title": a.title, "category": a.category, "issuer_event": a.issuer_event}
            for a in (await db.execute(ach_stmt)).scalars().all()
        ]

        return {
            "student_name": f"{user.first_name} {user.last_name}",
            "headline": port.headline,
            "bio": port.bio,
            "theme": port.theme,
            "contact_email": port.contact_email,
            "social_links": port.social_links,
            "custom_links": port.custom_links,
            "projects": [
                {
                    "id": p.id,
                    "title": p.title,
                    "short_description": p.short_description or p.description,
                    "project_type": p.project_type,
                    "technologies": p.technologies,
                    "repository_url": p.repository_url,
                    "live_url": p.live_url or p.demo_url,
                    "quality_score": p.quality_score,
                    "is_verified": p.is_verified,
                }
                for p in projects
            ],
            "skills": skills,
            "certifications": certs,
            "achievements": achievements,
        }


def uuid_tail() -> str:
    import uuid
    return uuid.uuid4().hex[:6]


project_intelligence_service = ProjectIntelligenceService()
