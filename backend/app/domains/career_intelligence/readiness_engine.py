"""Pure deterministic Career Readiness and Skill Gap Engine for Domain 7."""

from decimal import Decimal
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from app.domains.career_intelligence.config import CareerIntelligenceConfig, DEFAULT_CAREER_CONFIG


class CareerSkillReq(BaseModel):
    skill_id: str
    skill_name: str
    importance: str = "required"  # required, preferred, critical, bonus
    weight: Decimal = Field(default=Decimal("1.00"))
    min_proficiency: Decimal = Field(default=Decimal("0.6000"))


class SkillGapItem(BaseModel):
    skill_id: str
    skill_name: str
    importance: str
    current_proficiency: Decimal
    required_proficiency: Decimal
    gap_size: Decimal
    severity: str  # critical, high, medium, low, no_gap
    reason: str


class CareerReadinessCalculationResult(BaseModel):
    career_id: str
    career_title: str
    readiness_score: Decimal
    fit_score: Decimal
    confidence: Decimal
    required_skill_coverage: Decimal
    preferred_skill_coverage: Decimal
    critical_skill_coverage: Decimal
    gaps: List[SkillGapItem]
    critical_gaps: List[SkillGapItem]
    strengths: List[SkillGapItem]
    developing: List[SkillGapItem]
    status: str
    explanation: Dict[str, Any]
    algorithm_version: str


class CareerReadinessEngine:
    """Pure mathematical engine evaluating career readiness, gaps, and fit."""

    def __init__(self, config: Optional[CareerIntelligenceConfig] = None):
        self.config = config or DEFAULT_CAREER_CONFIG

    def calculate_readiness(
        self,
        career_id: str,
        career_title: str,
        requirements: List[CareerSkillReq],
        student_skill_proficiencies: Dict[str, Decimal],
        student_skill_confidences: Optional[Dict[str, Decimal]] = None,
        is_target_career_goal: bool = False,
    ) -> CareerReadinessCalculationResult:
        """Deterministically evaluates career readiness from canonical catalog requirements and student skill state.

        Formula:
          readiness = w_req * req_coverage + w_crit * crit_coverage + w_pref * pref_coverage
        """
        confidences = student_skill_confidences or {}

        if not requirements:
            return CareerReadinessCalculationResult(
                career_id=career_id,
                career_title=career_title,
                readiness_score=Decimal("0.0000"),
                fit_score=Decimal("0.5000") if is_target_career_goal else Decimal("0.0000"),
                confidence=Decimal("0.0000"),
                required_skill_coverage=Decimal("0.0000"),
                preferred_skill_coverage=Decimal("0.0000"),
                critical_skill_coverage=Decimal("0.0000"),
                gaps=[],
                critical_gaps=[],
                strengths=[],
                developing=[],
                status="insufficient_catalog_data",
                explanation={
                    "reason": "No skill mappings configured in CareerCatalog for this role.",
                    "requirements_count": 0,
                },
                algorithm_version=self.config.algorithm_version,
            )

        # Classify skill requirements by importance
        req_weights = Decimal("0.0000")
        req_attained = Decimal("0.0000")

        pref_weights = Decimal("0.0000")
        pref_attained = Decimal("0.0000")

        crit_count = 0
        crit_met = 0

        gaps: List[SkillGapItem] = []
        critical_gaps: List[SkillGapItem] = []
        strengths: List[SkillGapItem] = []
        developing: List[SkillGapItem] = []

        confidence_sum = Decimal("0.0000")

        for r in requirements:
            curr = student_skill_proficiencies.get(r.skill_id, Decimal("0.0000"))
            curr = max(Decimal("0.0000"), min(Decimal("1.0000"), curr))
            target = r.min_proficiency
            weight = r.weight

            gap = max(Decimal("0.0000"), target - curr)
            imp = r.importance.lower()

            # Attainment ratio: curr / target clamped to 1.0
            attainment = min(Decimal("1.0000"), curr / target) if target > Decimal("0.0") else Decimal("1.0000")

            if imp in ["required", "critical"]:
                req_weights += weight
                req_attained += attainment * weight
            else:
                pref_weights += weight
                pref_attained += attainment * weight

            if imp == "critical":
                crit_count += 1
                if curr >= target:
                    crit_met += 1

            # Gap severity classification
            t = self.config.gap_thresholds
            if gap <= Decimal("0.0000"):
                severity = "no_gap"
                reason = "Competency meets or exceeds career requirement."
            elif imp == "critical":
                severity = "critical"
                reason = "Critical career dependency below threshold."
            elif imp == "required" and gap >= t.critical_gap:
                severity = "critical"
                reason = "Required core career competency significantly below target."
            elif gap >= t.high_gap:
                severity = "high"
                reason = "Competency below target threshold."
            elif gap >= t.medium_gap:
                severity = "medium"
                reason = "Competency developing but requires reinforcement."
            else:
                severity = "low"
                reason = "Minor gap; near target proficiency."

            gap_item = SkillGapItem(
                skill_id=r.skill_id,
                skill_name=r.skill_name,
                importance=r.importance,
                current_proficiency=curr,
                required_proficiency=target,
                gap_size=gap,
                severity=severity,
                reason=reason,
            )

            gaps.append(gap_item)

            if severity == "critical":
                critical_gaps.append(gap_item)

            if gap <= Decimal("0.0000") and curr >= Decimal("0.6000"):
                strengths.append(gap_item)
            elif Decimal("0.3500") <= curr < target:
                developing.append(gap_item)

            confidence_sum += confidences.get(r.skill_id, Decimal("0.1000"))

        # Calculate coverages
        req_cov = (
            round(req_attained / req_weights, 4)
            if req_weights > Decimal("0.0")
            else Decimal("1.0000")
        )
        pref_cov = (
            round(pref_attained / pref_weights, 4)
            if pref_weights > Decimal("0.0")
            else Decimal("1.0000")
        )
        crit_cov = (
            round(Decimal(str(crit_met)) / Decimal(str(crit_count)), 4)
            if crit_count > 0
            else Decimal("1.0000")
        )

        rw = self.config.readiness_weights
        final_readiness = (
            rw.required_coverage_weight * req_cov
            + rw.critical_coverage_weight * crit_cov
            + rw.preferred_coverage_weight * pref_cov
        )
        final_readiness = max(Decimal("0.0000"), min(Decimal("1.0000"), round(final_readiness, 4)))

        # Fit score: career goal alignment (0.30) + skill affinity (0.70 * req_cov)
        goal_alignment = Decimal("1.0000") if is_target_career_goal else Decimal("0.3000")
        fit_score = round(Decimal("0.30") * goal_alignment + Decimal("0.70") * req_cov, 4)

        avg_confidence = round(confidence_sum / Decimal(str(len(requirements))), 4)

        status = (
            "assessed"
            if len(student_skill_proficiencies) > 0
            else "insufficient_student_evidence"
        )

        return CareerReadinessCalculationResult(
            career_id=career_id,
            career_title=career_title,
            readiness_score=final_readiness,
            fit_score=fit_score,
            confidence=avg_confidence,
            required_skill_coverage=req_cov,
            preferred_skill_coverage=pref_cov,
            critical_skill_coverage=crit_cov,
            gaps=gaps,
            critical_gaps=critical_gaps,
            strengths=strengths,
            developing=developing,
            status=status,
            explanation={
                "readiness_percentage": round(float(final_readiness) * 100, 1),
                "required_skill_coverage_pct": round(float(req_cov) * 100, 1),
                "critical_skill_coverage_pct": round(float(crit_cov) * 100, 1),
                "preferred_skill_coverage_pct": round(float(pref_cov) * 100, 1),
                "critical_skills_below_threshold": len(critical_gaps),
                "formula_weights": {
                    "required": float(rw.required_coverage_weight),
                    "critical": float(rw.critical_coverage_weight),
                    "preferred": float(rw.preferred_coverage_weight),
                },
            },
            algorithm_version=self.config.algorithm_version,
        )
