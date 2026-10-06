"""Centralized configuration for Domain 7: Skill Intelligence, Career Trajectories & Placement Readiness."""

from decimal import Decimal
from typing import Dict
from pydantic import BaseModel, Field


class SkillSourceWeights(BaseModel):
    """Deterministic evidence weighting per origin source."""
    assessment: Decimal = Field(default=Decimal("1.00"))
    coding_assessment: Decimal = Field(default=Decimal("1.10"))
    concept_mastery: Decimal = Field(default=Decimal("0.95"))
    project: Decimal = Field(default=Decimal("0.85"))
    faculty_verification: Decimal = Field(default=Decimal("0.90"))
    mentor_verification: Decimal = Field(default=Decimal("0.80"))
    course_completion: Decimal = Field(default=Decimal("0.65"))
    certification: Decimal = Field(default=Decimal("0.60"))
    self_report: Decimal = Field(default=Decimal("0.30"))


class ProficiencyTierThresholds(BaseModel):
    """Normalized proficiency tier cutoffs in [0.0, 1.0]."""
    exposure_max: Decimal = Field(default=Decimal("0.1999"))
    beginner_max: Decimal = Field(default=Decimal("0.3999"))
    developing_max: Decimal = Field(default=Decimal("0.5999"))
    proficient_max: Decimal = Field(default=Decimal("0.7999"))
    # >= 0.80 is advanced


class ReadinessWeights(BaseModel):
    """Component weights for authoritative career readiness calculation."""
    required_coverage_weight: Decimal = Field(default=Decimal("0.50"))
    critical_coverage_weight: Decimal = Field(default=Decimal("0.35"))
    preferred_coverage_weight: Decimal = Field(default=Decimal("0.15"))


class GapSeverityThresholds(BaseModel):
    """Thresholds for skill gap severity classification."""
    critical_gap: Decimal = Field(default=Decimal("0.40"))
    high_gap: Decimal = Field(default=Decimal("0.25"))
    medium_gap: Decimal = Field(default=Decimal("0.15"))


class CareerIntelligenceConfig(BaseModel):
    """Top-level configuration for Domain 7 intelligence calculation."""
    algorithm_version: str = "v1"
    source_weights: SkillSourceWeights = Field(default_factory=SkillSourceWeights)
    tiers: ProficiencyTierThresholds = Field(default_factory=ProficiencyTierThresholds)
    readiness_weights: ReadinessWeights = Field(default_factory=ReadinessWeights)
    gap_thresholds: GapSeverityThresholds = Field(default_factory=GapSeverityThresholds)
    confidence_saturation_count: int = 5
    min_evidence_for_verification: int = 2


DEFAULT_CAREER_CONFIG = CareerIntelligenceConfig()
