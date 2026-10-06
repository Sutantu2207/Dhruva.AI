"""Centralized, versioned configuration for Domain 6 Knowledge State & Mastery."""

from decimal import Decimal
from typing import Dict
from pydantic import BaseModel, Field


class EvidenceWeightConfig(BaseModel):
    """Deterministic multipliers for distinct learning evidence sources."""
    assessment: Decimal = Decimal("1.00")
    practice: Decimal = Decimal("0.80")
    recall: Decimal = Decimal("0.90")
    application: Decimal = Decimal("1.10")
    manual: Decimal = Decimal("0.70")
    lesson: Decimal = Decimal("0.60")

    def get_weight(self, evidence_type: str) -> Decimal:
        return getattr(self, evidence_type.lower(), Decimal("1.00"))


class DifficultyWeightConfig(BaseModel):
    """Deterministic multipliers for author-defined question difficulties."""
    easy: Decimal = Decimal("0.80")
    medium: Decimal = Decimal("1.00")
    hard: Decimal = Decimal("1.20")
    expert: Decimal = Decimal("1.40")

    def get_weight(self, difficulty: str) -> Decimal:
        return getattr(self, difficulty.lower(), Decimal("1.00"))


class MasteryThresholdConfig(BaseModel):
    """Thresholds for deterministic mastery state categorization."""
    mastered: Decimal = Decimal("0.8000")
    proficient: Decimal = Decimal("0.6000")
    developing: Decimal = Decimal("0.3000")
    at_risk_drop_threshold: Decimal = Decimal("0.2000")


class ConfidenceConfig(BaseModel):
    """Parameters governing deterministic confidence estimation."""
    min_evidence_count: int = 2
    scaling_k: float = 0.35
    variance_penalty_weight: float = 0.50


class RecencyDecayConfig(BaseModel):
    """Exponential time-decay parameters for historical evidence."""
    lambda_rate: float = 0.05  # Half-life of ~13.86 days
    min_decay_factor: float = 0.05


class RetentionConfig(BaseModel):
    """Exponential retention decay parameters based on Ebbinghaus forgetting model."""
    default_base_stability_days: float = 1.0


class SM2Config(BaseModel):
    """SuperMemo SM-2 algorithm constants."""
    initial_ease_factor: Decimal = Decimal("2.5000")
    min_ease_factor: Decimal = Decimal("1.3000")
    first_interval_days: int = 1
    second_interval_days: int = 6


class PriorityWeightConfig(BaseModel):
    """Deterministic weights for calculating student learning priority scores."""
    mastery_gap: Decimal = Decimal("0.3000")
    retention_risk: Decimal = Decimal("0.2500")
    review_urgency: Decimal = Decimal("0.2500")
    prerequisite_weakness: Decimal = Decimal("0.1000")
    recent_failure: Decimal = Decimal("0.1000")


class KnowledgeStateConfig(BaseModel):
    """Unified versioned configuration container."""
    algorithm_version: str = "v1"
    evidence_weights: EvidenceWeightConfig = Field(default_factory=EvidenceWeightConfig)
    difficulty_weights: DifficultyWeightConfig = Field(default_factory=DifficultyWeightConfig)
    mastery_thresholds: MasteryThresholdConfig = Field(default_factory=MasteryThresholdConfig)
    confidence: ConfidenceConfig = Field(default_factory=ConfidenceConfig)
    recency_decay: RecencyDecayConfig = Field(default_factory=RecencyDecayConfig)
    retention: RetentionConfig = Field(default_factory=RetentionConfig)
    sm2: SM2Config = Field(default_factory=SM2Config)
    priority_weights: PriorityWeightConfig = Field(default_factory=PriorityWeightConfig)


# Default singleton instance
DEFAULT_KNOWLEDGE_CONFIG = KnowledgeStateConfig()
