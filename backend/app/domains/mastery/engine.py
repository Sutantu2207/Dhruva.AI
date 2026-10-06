"""Deterministic Concept-Level Mastery Engine.

Calculates concept mastery scores [0.0, 1.0] and classifies mastery tiers.
Deterministic logic is the sole source of truth for student mastery.
"""

from enum import Enum
from typing import Dict, Any
from pydantic import BaseModel, Field


class MasteryTier(str, Enum):
    NOVICE = "novice"          # [0.00, 0.40)
    COMPETENT = "competent"    # [0.40, 0.70)
    PROFICIENT = "proficient"  # [0.70, 0.90)
    MASTER = "master"          # [0.90, 1.00]


class ConceptMasteryRecord(BaseModel):
    concept_id: str
    concept_name: str
    mastery_score: float = Field(ge=0.0, le=1.0)
    tier: MasteryTier
    assessments_completed: int
    confidence_weight: float = Field(ge=0.0, le=1.0)


def calculate_mastery_tier(score: float) -> MasteryTier:
    """Deterministic categorization of mastery score."""
    if score >= 0.90:
        return MasteryTier.MASTER
    elif score >= 0.70:
        return MasteryTier.PROFICIENT
    elif score >= 0.40:
        return MasteryTier.COMPETENT
    else:
        return MasteryTier.NOVICE


def compute_updated_mastery(
    current_score: float,
    assessment_score: float,
    weight: float = 0.25,
    decay_penalty: float = 0.0,
) -> float:
    """Updates mastery score using deterministic exponential moving average with decay.

    Formula: new_score = clamp((current_score * (1 - weight) + assessment_score * weight) - decay, 0.0, 1.0)
    """
    if not (0.0 <= weight <= 1.0):
        raise ValueError("Weight must be between 0.0 and 1.0")

    blended = (current_score * (1.0 - weight)) + (assessment_score * weight)
    adjusted = blended - decay_penalty
    return round(max(0.0, min(1.0, adjusted)), 4)
