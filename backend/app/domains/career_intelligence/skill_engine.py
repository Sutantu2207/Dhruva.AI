"""Pure deterministic Skill Intelligence Engine for Domain 7."""

from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.domains.career_intelligence.config import CareerIntelligenceConfig, DEFAULT_CAREER_CONFIG


class SkillEvidenceInput(BaseModel):
    source_type: str
    source_id: str
    score: Decimal = Field(ge=Decimal("0.0"), le=Decimal("1.0"))
    is_verified: bool = False
    weight_multiplier: Decimal = Field(default=Decimal("1.00"))


class EvaluatedSkillResult(BaseModel):
    skill_id: str
    observed_proficiency: Decimal
    self_reported_proficiency: Optional[Decimal]
    verified_proficiency: Decimal
    confidence: Decimal
    evidence_count: int
    verified_evidence_count: int
    assessment_evidence_count: int
    project_evidence_count: int
    course_evidence_count: int
    certification_evidence_count: int
    concept_mastery_contribution: Decimal
    verification_status: str
    proficiency_tier: str
    algorithm_version: str


class SkillIntelligenceEngine:
    """Pure mathematical engine computing authoritative skill proficiency and verification states."""

    def __init__(self, config: Optional[CareerIntelligenceConfig] = None):
        self.config = config or DEFAULT_CAREER_CONFIG

    def evaluate_skill(
        self,
        skill_id: str,
        evidence_items: List[SkillEvidenceInput],
        self_reported_proficiency: Optional[Decimal] = None,
        concept_mastery_score: Optional[Decimal] = None,
    ) -> EvaluatedSkillResult:
        """Deterministically evaluates a skill from all observed evidence records.

        Invariant: Same evidence records + same config -> identical result.
        """
        weights_cfg = self.config.source_weights

        total_weight = Decimal("0.0000")
        weighted_score_sum = Decimal("0.0000")

        verified_weight = Decimal("0.0000")
        verified_score_sum = Decimal("0.0000")

        asst_count = 0
        proj_count = 0
        course_count = 0
        cert_count = 0
        verified_count = 0

        scores_list: List[Decimal] = []

        # 1. Process concept mastery contribution if available
        concept_contrib = Decimal("0.0000")
        if concept_mastery_score is not None:
            c_score = max(Decimal("0.0"), min(Decimal("1.0"), concept_mastery_score))
            w = weights_cfg.concept_mastery
            concept_contrib = c_score
            total_weight += w
            weighted_score_sum += c_score * w
            scores_list.append(c_score)
            # Domain 6 concept mastery is verified by definition if backed by assessment
            verified_weight += w
            verified_score_sum += c_score * w
            verified_count += 1

        # 2. Process discrete evidence items
        for ev in evidence_items:
            s = max(Decimal("0.0"), min(Decimal("1.0"), ev.score))
            st = ev.source_type.lower()

            base_w = getattr(weights_cfg, st, Decimal("0.70"))
            w = base_w * ev.weight_multiplier

            total_weight += w
            weighted_score_sum += s * w
            scores_list.append(s)

            if st in ["assessment", "coding_assessment"]:
                asst_count += 1
            elif st == "project":
                proj_count += 1
            elif st == "course_completion":
                course_count += 1
            elif st == "certification":
                cert_count += 1

            if ev.is_verified:
                verified_count += 1
                verified_weight += w
                verified_score_sum += s * w

        # 3. Process self-reported proficiency with conservative weight if present
        if self_reported_proficiency is not None:
            sr = max(Decimal("0.0"), min(Decimal("1.0"), self_reported_proficiency))
            sr_w = weights_cfg.self_report
            total_weight += sr_w
            weighted_score_sum += sr * sr_w

        # Compute observed proficiency
        observed = (
            round(weighted_score_sum / total_weight, 4)
            if total_weight > Decimal("0.0")
            else Decimal("0.0000")
        )
        observed = max(Decimal("0.0000"), min(Decimal("1.0000"), observed))

        # Compute verified proficiency
        verified = (
            round(verified_score_sum / verified_weight, 4)
            if verified_weight > Decimal("0.0")
            else Decimal("0.0000")
        )
        verified = max(Decimal("0.0000"), min(Decimal("1.0000"), verified))

        # Compute confidence: sample saturation * variance penalty
        tot_count = len(evidence_items) + (1 if concept_mastery_score is not None else 0)
        sat_target = Decimal(str(self.config.confidence_saturation_count))
        sample_factor = min(Decimal("1.0000"), Decimal(str(tot_count)) / sat_target)

        # Variance penalty
        variance_penalty = Decimal("0.0000")
        if len(scores_list) >= 2:
            mean = sum(scores_list) / Decimal(str(len(scores_list)))
            var = sum((x - mean) ** 2 for x in scores_list) / Decimal(str(len(scores_list)))
            variance_penalty = min(Decimal("1.0000"), var * Decimal("2.0"))

        confidence = max(
            Decimal("0.0000"),
            min(Decimal("1.0000"), round(sample_factor * (Decimal("1.0000") - variance_penalty), 4)),
        )

        # Verification status classification
        if verified_count >= 3 and verified >= Decimal("0.75"):
            v_status = "certified"
        elif verified_count >= self.config.min_evidence_for_verification and verified >= Decimal("0.50"):
            v_status = "verified"
        elif verified_count >= 1:
            v_status = "partially_verified"
        else:
            v_status = "unverified"

        # Proficiency tier classification
        # Prefer verified proficiency if verified evidence exists, else observed
        effective_prof = verified if verified_count >= self.config.min_evidence_for_verification else observed
        tiers = self.config.tiers

        if effective_prof <= tiers.exposure_max:
            tier = "exposure"
        elif effective_prof <= tiers.beginner_max:
            tier = "beginner"
        elif effective_prof <= tiers.developing_max:
            tier = "developing"
        elif effective_prof <= tiers.proficient_max:
            tier = "proficient"
        else:
            tier = "advanced"

        return EvaluatedSkillResult(
            skill_id=skill_id,
            observed_proficiency=observed,
            self_reported_proficiency=self_reported_proficiency,
            verified_proficiency=verified,
            confidence=confidence,
            evidence_count=tot_count,
            verified_evidence_count=verified_count,
            assessment_evidence_count=asst_count,
            project_evidence_count=proj_count,
            course_evidence_count=course_count,
            certification_evidence_count=cert_count,
            concept_mastery_contribution=concept_contrib,
            verification_status=v_status,
            proficiency_tier=tier,
            algorithm_version=self.config.algorithm_version,
        )
