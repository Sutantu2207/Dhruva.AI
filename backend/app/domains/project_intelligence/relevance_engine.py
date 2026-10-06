"""Pure deterministic Career Relevance Engine for Domain 8.

Evaluates how strongly a student project aligns with a specific or primary target career pathway.
Uses canonical CareerSkillMapping requirements to evaluate practical overlap.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CareerSkillRequirementItem:
    """Canonical career requirement item."""
    skill_id: str
    skill_name: str
    importance: str  # critical, required, preferred
    weight: float = 1.0


@dataclass(frozen=True)
class CareerRelevanceResult:
    """Deterministic career relevance calculation."""
    career_id: str
    career_title: str
    relevance_score: float  # 0 to 100
    relevance_tier: str  # high, medium, low, none
    aligned_skills_count: int
    critical_aligned_count: int
    total_career_skills_count: int
    aligned_skills: List[Dict[str, Any]]
    critical_matches: List[Dict[str, Any]]
    remaining_career_gaps: List[Dict[str, Any]]
    project_auxiliary_skills: List[Dict[str, Any]]
    explanation: str
    algorithm_version: str = "v1.0.0-deterministic"


class CareerRelevanceEngine:
    """Evaluates the alignment of a student project against target career requirements."""

    def __init__(self, algorithm_version: str = "v1.0.0-deterministic"):
        self.algorithm_version = algorithm_version

    def evaluate_relevance(
        self,
        project_id: str,
        project_title: str,
        project_skill_ids: List[str],
        project_skill_names: Dict[str, str],
        career_id: str,
        career_title: str,
        career_requirements: List[CareerSkillRequirementItem],
    ) -> CareerRelevanceResult:
        if not career_requirements:
            return CareerRelevanceResult(
                career_id=career_id,
                career_title=career_title,
                relevance_score=0.0,
                relevance_tier="none",
                aligned_skills_count=0,
                critical_aligned_count=0,
                total_career_skills_count=0,
                aligned_skills=[],
                critical_matches=[],
                remaining_career_gaps=[],
                project_auxiliary_skills=[
                    {"skill_id": sid, "skill_name": project_skill_names.get(sid, sid)}
                    for sid in project_skill_ids
                ],
                explanation=f"Career '{career_title}' has no mapped skill requirements in the catalog.",
                algorithm_version=self.algorithm_version,
            )

        project_skills_set = set(project_skill_ids)
        aligned_skills: List[Dict[str, Any]] = []
        critical_matches: List[Dict[str, Any]] = []
        remaining_career_gaps: List[Dict[str, Any]] = []

        total_weight = 0.0
        matched_weight = 0.0

        for req in career_requirements:
            # Importance multiplier
            mult = 1.5 if req.importance == "critical" else (1.0 if req.importance == "required" else 0.5)
            eff_weight = req.weight * mult
            total_weight += eff_weight

            if req.skill_id in project_skills_set:
                matched_weight += eff_weight
                item = {
                    "skill_id": req.skill_id,
                    "skill_name": req.skill_name,
                    "importance": req.importance,
                    "weight": req.weight,
                }
                aligned_skills.append(item)
                if req.importance == "critical":
                    critical_matches.append(item)
            else:
                remaining_career_gaps.append({
                    "skill_id": req.skill_id,
                    "skill_name": req.skill_name,
                    "importance": req.importance,
                })

        auxiliary_skills = [
            {"skill_id": sid, "skill_name": project_skill_names.get(sid, sid)}
            for sid in project_skill_ids
            if sid not in {r.skill_id for r in career_requirements}
        ]

        if total_weight > 0.0:
            relevance_score = round(min(100.0, (matched_weight / total_weight) * 100.0), 2)
        else:
            relevance_score = 0.0

        # Classify tier
        if relevance_score >= 50.0 or len(critical_matches) >= 2:
            relevance_tier = "high"
            explanation = (
                f"Project demonstrates strong practical alignment with {career_title}. "
                f"Covers {len(aligned_skills)} of {len(career_requirements)} target competencies including {len(critical_matches)} critical skills."
            )
        elif relevance_score >= 20.0 or len(aligned_skills) >= 1:
            relevance_tier = "medium"
            explanation = (
                f"Project moderately reinforces {career_title}. "
                f"Covers {len(aligned_skills)} target skills, while {len(remaining_career_gaps)} core competencies remain to be demonstrated."
            )
        elif relevance_score > 0.0:
            relevance_tier = "low"
            explanation = f"Project tangentially touches {len(aligned_skills)} skill related to {career_title}."
        else:
            relevance_tier = "none"
            explanation = f"Project skills do not directly overlap with {career_title} catalog requirements."

        return CareerRelevanceResult(
            career_id=career_id,
            career_title=career_title,
            relevance_score=relevance_score,
            relevance_tier=relevance_tier,
            aligned_skills_count=len(aligned_skills),
            critical_aligned_count=len(critical_matches),
            total_career_skills_count=len(career_requirements),
            aligned_skills=aligned_skills,
            critical_matches=critical_matches,
            remaining_career_gaps=remaining_career_gaps,
            project_auxiliary_skills=auxiliary_skills,
            explanation=explanation,
            algorithm_version=self.algorithm_version,
        )
