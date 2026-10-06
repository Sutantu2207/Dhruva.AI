"""Deterministic Career Intelligence & Skill-Gap Analysis Engine.

Performs mathematical skill-gap analysis, readiness scoring, and deterministic career fit.
The LLM is NOT permitted to invent readiness scores or career recommendations.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SkillRequirement(BaseModel):
    skill_id: str
    skill_name: str
    target_proficiency: float = Field(ge=0.0, le=1.0)
    importance_weight: float = Field(default=1.0, gt=0)


class CareerTargetProfile(BaseModel):
    career_id: str
    title: str
    domain: str
    required_skills: List[SkillRequirement]


class SkillGapItem(BaseModel):
    skill_id: str
    skill_name: str
    current_proficiency: float
    target_proficiency: float
    gap: float
    is_critical: bool


class CareerReadinessReport(BaseModel):
    career_id: str
    career_title: str
    readiness_score: float = Field(ge=0.0, le=100.0)
    confidence_value: float = Field(ge=0.0, le=1.0)
    skill_gaps: List[SkillGapItem]
    verified_evidence_count: int


def calculate_career_readiness(
    target_profile: CareerTargetProfile,
    student_skills: Dict[str, float],
    verified_evidence_count: int = 1,
) -> CareerReadinessReport:
    """Computes deterministic readiness score and skill gaps.

    Formula:
      readiness = sum(min(curr, target) / target * weight) / sum(weight) * 100
      gap = max(0.0, target - curr)
      critical = gap > 0.35 and weight >= 1.0
    """
    if not target_profile.required_skills:
        return CareerReadinessReport(
            career_id=target_profile.career_id,
            career_title=target_profile.title,
            readiness_score=0.0,
            confidence_value=0.0,
            skill_gaps=[],
            verified_evidence_count=verified_evidence_count,
        )

    total_weight = 0.0
    achieved_weight = 0.0
    gaps: List[SkillGapItem] = []

    for req in target_profile.required_skills:
        curr = student_skills.get(req.skill_id, 0.0)
        curr = max(0.0, min(1.0, curr))
        target = req.target_proficiency
        weight = req.importance_weight

        # Cap attainment at target proficiency for readiness calculation
        attainment = min(curr, target) / target if target > 0 else 1.0
        achieved_weight += attainment * weight
        total_weight += weight

        gap_value = round(max(0.0, target - curr), 4)
        is_critical = gap_value > 0.35 and weight >= 1.0

        gaps.append(
            SkillGapItem(
                skill_id=req.skill_id,
                skill_name=req.skill_name,
                current_proficiency=round(curr, 4),
                target_proficiency=target,
                gap=gap_value,
                is_critical=is_critical,
            )
        )

    readiness = round((achieved_weight / total_weight) * 100.0, 2) if total_weight > 0 else 0.0

    # Deterministic confidence based on evidence count
    confidence = round(min(1.0, 0.2 + (verified_evidence_count * 0.15)), 4)

    return CareerReadinessReport(
        career_id=target_profile.career_id,
        career_title=target_profile.title,
        readiness_score=readiness,
        confidence_value=confidence,
        skill_gaps=gaps,
        verified_evidence_count=verified_evidence_count,
    )
