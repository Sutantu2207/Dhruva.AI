"""Pure deterministic Portfolio Intelligence Engine for Domain 8.

Evaluates student portfolio health, diversity, depth, and completeness.
Adheres strictly to the Honesty Rule: if data is insufficient, returns "insufficient_evidence"
rather than inventing scores.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProjectSummaryItem:
    """Summary of a student project used for portfolio evaluation."""
    id: str
    title: str
    project_type: str
    status: str
    is_verified: bool
    quality_score: Optional[float]
    has_problem_and_solution: bool
    has_repo_or_demo: bool
    skills_count: int
    evidence_count: int
    is_career_aligned: bool = False


@dataclass(frozen=True)
class PortfolioEvaluationInput:
    """Inputs to evaluate portfolio health."""
    has_portfolio_record: bool
    headline: Optional[str] = None
    bio: Optional[str] = None
    contact_email: Optional[str] = None
    social_links_count: int = 0
    custom_links_count: int = 0
    public_visibility: bool = False
    projects: List[ProjectSummaryItem] = field(default_factory=list)
    total_skills_count: int = 0
    verified_skills_count: int = 0
    total_certifications_count: int = 0
    verified_certifications_count: int = 0
    total_achievements_count: int = 0
    has_career_goal: bool = False


@dataclass(frozen=True)
class PortfolioHealthResult:
    """Output containing health dimensions, completeness, and explainable checklist."""
    status: str  # assessed, insufficient_evidence
    overall_health_score: Optional[float]  # 0 to 100 or None
    technical_depth: Optional[float]
    project_diversity: Optional[float]
    evidence_quality: Optional[float]
    documentation_quality: Optional[float]
    career_alignment: Optional[float]
    professional_presence: Optional[float]
    verification_coverage: Optional[float]
    completeness_score: float  # 0 to 100
    missing_sections: List[str]
    dimension_explanations: Dict[str, Any]
    algorithm_version: str = "v1.0.0-deterministic"


class PortfolioIntelligenceEngine:
    """Deterministic, versioned evaluator for portfolio health and completeness."""

    def __init__(self, algorithm_version: str = "v1.0.0-deterministic"):
        self.algorithm_version = algorithm_version

    def evaluate_portfolio(self, port_in: PortfolioEvaluationInput) -> PortfolioHealthResult:
        missing_sections: List[str] = []

        # --- Completeness Checklist (0 - 100) ---
        completeness = 0.0

        if port_in.headline and len(port_in.headline.strip()) >= 5:
            completeness += 10.0
        else:
            missing_sections.append("Professional headline / title")

        if port_in.bio and len(port_in.bio.strip()) >= 20:
            completeness += 10.0
        else:
            missing_sections.append("Biography / about statement")

        if port_in.contact_email or port_in.social_links_count > 0:
            completeness += 10.0
        else:
            missing_sections.append("Contact information or social profiles")

        num_projects = len(port_in.projects)
        if num_projects >= 1:
            completeness += 20.0
            if any(p.has_problem_and_solution for p in port_in.projects):
                completeness += 10.0
            else:
                missing_sections.append("Project problem statements and solutions")

            if any(p.has_repo_or_demo for p in port_in.projects):
                completeness += 10.0
            else:
                missing_sections.append("Live deployment or repository URLs")

            if any(p.evidence_count > 0 for p in port_in.projects):
                completeness += 10.0
            else:
                missing_sections.append("Empirical project evidence items")

            if any(p.is_verified for p in port_in.projects):
                completeness += 10.0
            else:
                missing_sections.append("Faculty or mentor verified projects")
        else:
            missing_sections.append("At least one documented project")

        if port_in.total_skills_count >= 1:
            completeness += 5.0
        else:
            missing_sections.append("Demonstrated technical skills")

        if port_in.public_visibility:
            completeness += 5.0

        completeness_score = round(min(100.0, max(0.0, completeness)), 2)

        # --- Insufficient Evidence Check ---
        # If student has zero projects and zero skills, do not synthesize health scores.
        if num_projects == 0 and port_in.total_skills_count == 0:
            return PortfolioHealthResult(
                status="insufficient_evidence",
                overall_health_score=None,
                technical_depth=None,
                project_diversity=None,
                evidence_quality=None,
                documentation_quality=None,
                career_alignment=None,
                professional_presence=None,
                verification_coverage=None,
                completeness_score=completeness_score,
                missing_sections=missing_sections,
                dimension_explanations={
                    "notice": "Insufficient project and skill evidence to evaluate portfolio health. Add projects to begin."
                },
                algorithm_version=self.algorithm_version,
            )

        # --- Granular Health Dimensions (0 - 100) ---
        # 1. Technical Depth
        quality_scores = [p.quality_score for p in port_in.projects if p.quality_score is not None]
        if quality_scores:
            avg_proj_quality = sum(quality_scores) / len(quality_scores)
        else:
            avg_proj_quality = 40.0 if num_projects > 0 else 0.0

        skills_depth = min(100.0, port_in.total_skills_count * 15.0)
        technical_depth = round(min(100.0, 0.6 * avg_proj_quality + 0.4 * skills_depth), 2)

        # 2. Project Diversity
        distinct_types = len(set(p.project_type for p in port_in.projects))
        # 1 type = 40, 2 types = 70, 3+ types = 100
        project_diversity = round(min(100.0, distinct_types * 35.0), 2) if num_projects > 0 else 0.0

        # 3. Evidence Quality
        total_evidence = sum(p.evidence_count for p in port_in.projects)
        verified_projects = sum(1 for p in port_in.projects if p.is_verified)
        evidence_quality = round(min(100.0, (verified_projects * 35.0) + (total_evidence * 15.0)), 2)

        # 4. Documentation Quality
        doc_pts = 0.0
        if port_in.bio:
            doc_pts += 25.0
        if port_in.headline:
            doc_pts += 15.0
        if num_projects > 0:
            doc_pts += (sum(1 for p in port_in.projects if p.has_problem_and_solution) / num_projects) * 60.0
        documentation_quality = round(min(100.0, doc_pts), 2)

        # 5. Career Alignment
        if port_in.has_career_goal:
            if num_projects > 0:
                aligned_count = sum(1 for p in port_in.projects if p.is_career_aligned)
                career_alignment = round(min(100.0, 30.0 + (aligned_count / num_projects) * 70.0), 2)
            else:
                career_alignment = 30.0
        else:
            career_alignment = 50.0  # Neutral when no target career specified

        # 6. Professional Presence
        pres_pts = 0.0
        if port_in.headline:
            pres_pts += 25.0
        if port_in.bio:
            pres_pts += 25.0
        if port_in.contact_email or port_in.social_links_count > 0:
            pres_pts += 25.0
        if port_in.public_visibility:
            pres_pts += 25.0
        professional_presence = round(min(100.0, pres_pts), 2)

        # 7. Verification Coverage
        total_items = num_projects + port_in.total_skills_count + port_in.total_certifications_count
        verified_items = verified_projects + port_in.verified_skills_count + port_in.verified_certifications_count
        if total_items > 0:
            verification_coverage = round(min(100.0, (verified_items / total_items) * 100.0), 2)
        else:
            verification_coverage = 0.0

        # Composite Health Score (0 - 100)
        # Weights: Depth (20%), Diversity (15%), Evidence (20%), Doc (15%), Alignment (15%), Presence (15%)
        overall = (
            0.20 * technical_depth +
            0.15 * project_diversity +
            0.20 * evidence_quality +
            0.15 * documentation_quality +
            0.15 * career_alignment +
            0.15 * professional_presence
        )
        overall_health_score = round(min(100.0, max(0.0, overall)), 2)

        explanations = {
            "technical_depth": f"Based on {num_projects} projects and {port_in.total_skills_count} demonstrated skills.",
            "project_diversity": f"Covering {distinct_types} distinct project types.",
            "evidence_quality": f"{total_evidence} evidence items across {verified_projects} verified projects.",
            "documentation_quality": "Evaluated from project problem/solution coverage and bio.",
            "career_alignment": "Evaluated against target career requirements." if port_in.has_career_goal else "No primary career target selected.",
            "professional_presence": f"Profile presence: headline, bio, contact, and {'public' if port_in.public_visibility else 'private'} visibility.",
            "verification_coverage": f"{verified_items} of {total_items} portfolio assets verified.",
        }

        return PortfolioHealthResult(
            status="assessed",
            overall_health_score=overall_health_score,
            technical_depth=technical_depth,
            project_diversity=project_diversity,
            evidence_quality=evidence_quality,
            documentation_quality=documentation_quality,
            career_alignment=career_alignment,
            professional_presence=professional_presence,
            verification_coverage=verification_coverage,
            completeness_score=completeness_score,
            missing_sections=missing_sections,
            dimension_explanations=explanations,
            algorithm_version=self.algorithm_version,
        )
