"""Deterministic Concept Mastery Engine.

Transforms authoritative learning evidence records into explainable, reproducible
mastery scores [0.0000, 1.0000], confidence estimates, states, and trends.
Pure deterministic logic is the sole source of truth. AI is strictly excluded.
"""

import math
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.domains.mastery.config import KnowledgeStateConfig, DEFAULT_KNOWLEDGE_CONFIG


class EvidenceItemDTO(BaseModel):
    """Normalized evidence record input for mastery evaluation."""
    id: str
    concept_id: str
    score: Decimal
    max_score: Decimal = Decimal("1.0000")
    evidence_type: str = "assessment"
    difficulty: str = "medium"
    timestamp: datetime


class MasteryEvaluationOutput(BaseModel):
    """Pure deterministic output of the concept mastery engine."""
    concept_id: str
    mastery: Optional[Decimal] = None  # None indicates insufficient evidence / unknown
    confidence: Decimal = Decimal("0.0000")
    state: str = "unknown"
    trend: str = "insufficient_data"
    evidence_count: int = 0
    effective_count: float = 0.0
    first_evidence_at: Optional[datetime] = None
    last_evidence_at: Optional[datetime] = None
    last_successful_at: Optional[datetime] = None
    last_failed_at: Optional[datetime] = None
    explanation_factors: Dict[str, Any] = Field(default_factory=dict)


class ConceptMasteryEngine:
    """Pure deterministic engine evaluating student concept mastery."""

    @staticmethod
    def evaluate(
        concept_id: str,
        evidence_items: List[EvidenceItemDTO],
        previous_state: Optional[str] = None,
        config: KnowledgeStateConfig = DEFAULT_KNOWLEDGE_CONFIG,
        now: Optional[datetime] = None,
    ) -> MasteryEvaluationOutput:
        """Evaluates concept mastery from historical evidence without external side effects."""
        if now is None:
            now = datetime.now(timezone.utc)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        if not evidence_items:
            return MasteryEvaluationOutput(
                concept_id=concept_id,
                mastery=None,
                confidence=Decimal("0.0000"),
                state="unknown",
                trend="insufficient_data",
                evidence_count=0,
                explanation_factors={
                    "reason": "No evidence observations recorded.",
                    "formula": "insufficient_evidence",
                },
            )

        # Sort chronologically
        sorted_evidence = sorted(evidence_items, key=lambda x: x.timestamp)
        evidence_count = len(sorted_evidence)
        first_evidence_at = sorted_evidence[0].timestamp
        last_evidence_at = sorted_evidence[-1].timestamp

        last_successful_at: Optional[datetime] = None
        last_failed_at: Optional[datetime] = None

        weighted_score_sum = 0.0
        total_weight_sum = 0.0
        normalized_scores: List[float] = []
        effective_weights: List[float] = []

        lambda_decay = config.recency_decay.lambda_rate

        for ev in sorted_evidence:
            score_ratio = float(ev.score / ev.max_score) if ev.max_score > 0 else 0.0
            score_ratio = max(0.0, min(1.0, score_ratio))
            normalized_scores.append(score_ratio)

            if score_ratio >= 0.60:
                last_successful_at = ev.timestamp
            else:
                last_failed_at = ev.timestamp

            # 1. Base Type Weight
            w_type = float(config.evidence_weights.get_weight(ev.evidence_type))
            # 2. Difficulty Weight
            w_diff = float(config.difficulty_weights.get_weight(ev.difficulty))

            # 3. Recency Time Decay (Exponential)
            ev_time = ev.timestamp if ev.timestamp.tzinfo is not None else ev.timestamp.replace(tzinfo=timezone.utc)
            elapsed_days = max(0.0, (now - ev_time).total_seconds() / 86400.0)
            decay_factor = max(
                config.recency_decay.min_decay_factor,
                math.exp(-lambda_decay * elapsed_days),
            )

            effective_weight = w_type * w_diff * decay_factor
            effective_weights.append(effective_weight)

            weighted_score_sum += score_ratio * effective_weight
            total_weight_sum += effective_weight

        effective_count = round(sum(effective_weights), 2)

        # Insufficient data handling: If fewer than min_evidence_count, do not assign definitive mastery
        if evidence_count < config.confidence.min_evidence_count:
            initial_score = normalized_scores[-1]
            return MasteryEvaluationOutput(
                concept_id=concept_id,
                mastery=Decimal(str(round(initial_score, 4))),
                confidence=Decimal("0.2000"),
                state="introduced" if evidence_count == 1 else "unknown",
                trend="insufficient_data",
                evidence_count=evidence_count,
                effective_count=effective_count,
                first_evidence_at=first_evidence_at,
                last_evidence_at=last_evidence_at,
                last_successful_at=last_successful_at,
                last_failed_at=last_failed_at,
                explanation_factors={
                    "reason": f"Only {evidence_count} evidence record(s) observed. Minimum required: {config.confidence.min_evidence_count}.",
                    "observations": evidence_count,
                    "state": "introduced" if evidence_count == 1 else "unknown",
                },
            )

        # Authoritative weighted average mastery
        calculated_mastery = weighted_score_sum / total_weight_sum if total_weight_sum > 0 else 0.0
        calculated_mastery = max(0.0, min(1.0, calculated_mastery))
        mastery_decimal = Decimal(str(round(calculated_mastery, 4)))

        # Confidence Calculation
        # Deterministic function of effective evidence count and score variance
        count_confidence = 1.0 - math.exp(-config.confidence.scaling_k * effective_count)

        # Variance calculation
        mean_score = sum(normalized_scores) / len(normalized_scores)
        variance = sum((s - mean_score) ** 2 for s in normalized_scores) / len(normalized_scores)
        consistency_multiplier = max(0.50, 1.0 - (config.confidence.variance_penalty_weight * math.sqrt(variance)))

        raw_confidence = max(0.0, min(1.0, count_confidence * consistency_multiplier))
        confidence_decimal = Decimal(str(round(raw_confidence, 4)))

        # Trend Calculation
        # Compare weighted recent window (last 3 items or latest 40% of observations) against older baseline
        split_idx = max(1, len(normalized_scores) - 3)
        if split_idx >= len(normalized_scores):
            trend = "stable"
        else:
            recent_scores = normalized_scores[split_idx:]
            historical_scores = normalized_scores[:split_idx]
            recent_avg = sum(recent_scores) / len(recent_scores)
            historical_avg = sum(historical_scores) / len(historical_scores)
            diff = recent_avg - historical_avg

            if diff >= 0.15:
                trend = "strongly_improving"
            elif diff >= 0.05:
                trend = "improving"
            elif diff <= -0.15:
                trend = "strongly_declining"
            elif diff <= -0.05:
                trend = "declining"
            else:
                trend = "stable"

        # Deterministic State Classification
        th = config.mastery_thresholds
        if calculated_mastery >= float(th.mastered) and raw_confidence >= 0.50:
            state = "mastered"
        elif calculated_mastery >= float(th.proficient):
            state = "proficient"
        elif calculated_mastery >= float(th.developing):
            state = "developing"
        else:
            state = "developing"

        # At-risk state detection: If previously mastered or proficient, but recent performance dropped severely
        if previous_state in ("mastered", "proficient") and (trend in ("declining", "strongly_declining") or calculated_mastery < float(th.proficient)):
            state = "at_risk"

        explanation_factors = {
            "evidence_count": evidence_count,
            "effective_evidence_weight": effective_count,
            "weighted_average_score": float(mastery_decimal),
            "recent_score_trend": trend,
            "variance_index": round(variance, 4),
            "confidence_metric": float(confidence_decimal),
            "classified_state": state,
            "algorithm_version": config.algorithm_version,
        }

        return MasteryEvaluationOutput(
            concept_id=concept_id,
            mastery=mastery_decimal,
            confidence=confidence_decimal,
            state=state,
            trend=trend,
            evidence_count=evidence_count,
            effective_count=effective_count,
            first_evidence_at=first_evidence_at,
            last_evidence_at=last_evidence_at,
            last_successful_at=last_successful_at,
            last_failed_at=last_failed_at,
            explanation_factors=explanation_factors,
        )
