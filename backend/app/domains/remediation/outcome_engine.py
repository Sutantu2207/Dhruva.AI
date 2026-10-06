"""Deterministic Outcome & Closed-Loop Closure Engine (Domain 10).

Measures post-remediation delta:
improvement_delta = mastery_after - mastery_before

Categorizes outcome strictly from observable evidence:
- IMPROVED: delta >= +0.15 OR mastery_after >= threshold
- PARTIALLY_IMPROVED: 0.05 <= delta < 0.15
- NO_SIGNIFICANT_CHANGE: -0.05 < delta < 0.05
- REGRESSED: delta <= -0.05
- INSUFFICIENT_EVIDENCE: mastery_after is None or evidence count unchanged

Deterministic plan closure rules:
- CLOSE_SUCCESS: target mastery >= threshold AND no unresolved blocking prerequisites
- CONTINUE: mastery improved but remains below threshold
- ESCALATE: repeated remediation attempts failed or prerequisite remains blocked

LANGUAGE INVARIANT: Uses "Observed improvement following remediation" — never "caused".
"""

from decimal import Decimal
from typing import Dict, Any, Optional
from app.domains.remediation.config import (
    MASTERY_PROFICIENCY_THRESHOLD,
    PREREQUISITE_READINESS_THRESHOLD,
    ALGORITHM_VERSION,
)


class OutcomeEngine:
    """Pure and deterministic remediation outcome calculation engine."""

    @staticmethod
    def evaluate_outcome(
        mastery_before: Optional[Decimal],
        mastery_after: Optional[Decimal],
        confidence_before: Decimal,
        confidence_after: Decimal,
        retention_before: Decimal,
        retention_after: Decimal,
        assessment_score_before: Optional[Decimal] = None,
        assessment_score_after: Optional[Decimal] = None,
        prerequisite_blocking: bool = False,
        attempt_count: int = 1,
    ) -> Dict[str, Any]:
        """Calculates observable improvement delta and authoritative closure decision."""
        if mastery_after is None:
            return {
                "outcome_status": "INSUFFICIENT_EVIDENCE",
                "improvement_delta": Decimal("0.0000"),
                "closure_decision": "CONTINUE",
                "closure_reason": "Insufficient post-reassessment evidence to verify mastery update.",
                "algorithm_version": ALGORITHM_VERSION,
            }

        m_before = mastery_before if mastery_before is not None else Decimal("0.0000")
        delta = (mastery_after - m_before).quantize(Decimal("0.0001"))

        # 1. Determine outcome classification
        if delta >= Decimal("0.1500") or mastery_after >= MASTERY_PROFICIENCY_THRESHOLD:
            outcome_status = "IMPROVED"
        elif delta >= Decimal("0.0500"):
            outcome_status = "PARTIALLY_IMPROVED"
        elif delta <= Decimal("-0.0500"):
            outcome_status = "REGRESSED"
        else:
            outcome_status = "NO_SIGNIFICANT_CHANGE"

        # 2. Determine deterministic closure decision
        if mastery_after >= MASTERY_PROFICIENCY_THRESHOLD and not prerequisite_blocking:
            closure_decision = "CLOSE_SUCCESS"
            closure_reason = (
                f"Observed post-remediation mastery reached {float(mastery_after):.2f}, "
                f"exceeding target proficiency threshold of {float(MASTERY_PROFICIENCY_THRESHOLD):.2f}. "
                "Foundational prerequisites satisfied."
            )
        elif outcome_status == "REGRESSED" or (attempt_count >= 3 and mastery_after < MASTERY_PROFICIENCY_THRESHOLD):
            closure_decision = "ESCALATE"
            closure_reason = (
                f"Observed repeated deficiency across {attempt_count} attempts. "
                "Deterministic automated remediation exhausted; faculty manual intervention required."
            )
        else:
            closure_decision = "CONTINUE"
            closure_reason = (
                f"Observed improvement delta of {float(delta):+.2f}, but current mastery ({float(mastery_after):.2f}) "
                f"remains below proficiency threshold of {float(MASTERY_PROFICIENCY_THRESHOLD):.2f}."
            )

        return {
            "outcome_status": outcome_status,
            "improvement_delta": delta,
            "closure_decision": closure_decision,
            "closure_reason": closure_reason,
            "mastery_before": mastery_before,
            "mastery_after": mastery_after,
            "confidence_before": confidence_before,
            "confidence_after": confidence_after,
            "retention_before": retention_before,
            "retention_after": retention_after,
            "assessment_score_before": assessment_score_before,
            "assessment_score_after": assessment_score_after,
            "algorithm_version": ALGORITHM_VERSION,
        }
