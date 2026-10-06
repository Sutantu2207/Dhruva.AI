"""Deterministic Early Intervention Signal Engine for identifying observable academic distress."""

from datetime import datetime, timezone, date
from typing import List, Dict, Any, Optional


class InterventionSignalEngine:
    """Pure deterministic engine detecting observable academic distress signals.

    Invariants:
    - Never generates psychological, emotional, or speculative judgments.
    - Strictly maps observable academic facts to actionable support recommendations.
    - Explainable, reproducible, and versioned.
    """

    ALGORITHM_VERSION = "v1.0.0-deterministic"

    @classmethod
    def evaluate_student_signals(
        cls,
        *,
        assessment_attempts: List[Dict[str, Any]],
        concept_states: List[Dict[str, Any]],
        overdue_reviews: List[Dict[str, Any]],
        lesson_progress: List[Dict[str, Any]],
        prerequisite_checks: List[Dict[str, Any]],
        project_skills: List[Dict[str, Any]],
        days_since_last_activity: Optional[int] = None,
        now: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Scans factual student records and yields deterministic signal specs."""
        now_dt = now or datetime.now(timezone.utc)
        signals: List[Dict[str, Any]] = []

        # 1. Repeated Assessment Failures
        completed_attempts = [
            a for a in assessment_attempts if a.get("status") in ("evaluated", "submitted")
        ]
        failed_attempts = [
            a for a in completed_attempts if a.get("is_passed") is False or (a.get("percentage") is not None and float(a["percentage"]) < 50.0)
        ]

        if len(failed_attempts) >= 3:
            signals.append({
                "signal_type": "repeated_assessment_failures",
                "severity": "urgent",
                "title": f"High Assessment Failure Frequency ({len(failed_attempts)} failed attempts)",
                "evidence_data": {
                    "total_attempts": len(completed_attempts),
                    "failed_count": len(failed_attempts),
                    "failed_assessment_ids": [a.get("assessment_id") or a.get("id") for a in failed_attempts[-3:]],
                },
                "recommended_action": "Schedule comprehensive faculty review and diagnostic assessment.",
                "algorithm_version": cls.ALGORITHM_VERSION,
            })
        elif len(failed_attempts) >= 2:
            signals.append({
                "signal_type": "repeated_assessment_failures",
                "severity": "high",
                "title": f"Multiple Assessment Failures ({len(failed_attempts)} failed attempts)",
                "evidence_data": {
                    "total_attempts": len(completed_attempts),
                    "failed_count": len(failed_attempts),
                    "failed_assessment_ids": [a.get("assessment_id") or a.get("id") for a in failed_attempts],
                },
                "recommended_action": "Recommend faculty mentoring and remedial topic practice.",
                "algorithm_version": cls.ALGORITHM_VERSION,
            })

        # 2. Persistent Low Concept Mastery
        low_mastery_concepts = [
            c for c in concept_states if float(c.get("mastery_score", 0.0)) < 0.40
        ]
        if len(low_mastery_concepts) >= 3:
            severity = "urgent" if len(low_mastery_concepts) >= 5 else "high"
            signals.append({
                "signal_type": "persistent_low_concept_mastery",
                "severity": severity,
                "title": f"Persistent Low Mastery Across {len(low_mastery_concepts)} Concepts",
                "evidence_data": {
                    "total_evaluated_concepts": len(concept_states),
                    "low_mastery_count": len(low_mastery_concepts),
                    "concept_ids": [c.get("concept_id") for c in low_mastery_concepts[:5]],
                },
                "recommended_action": "Assign targeted remedial lessons and interactive practice exercises.",
                "algorithm_version": cls.ALGORITHM_VERSION,
            })

        # 3. Overdue Spaced Repetition Reviews
        severely_overdue = [
            r for r in overdue_reviews if int(r.get("days_overdue", 0)) >= 5
        ]
        if len(severely_overdue) >= 3:
            signals.append({
                "signal_type": "overdue_reviews",
                "severity": "medium",
                "title": f"{len(severely_overdue)} Spaced Repetition Reviews Severely Overdue",
                "evidence_data": {
                    "overdue_count": len(severely_overdue),
                    "max_days_overdue": max((int(r.get("days_overdue", 0)) for r in severely_overdue), default=5),
                },
                "recommended_action": "Trigger automated daily learning mission reminder to prevent memory retention decay.",
                "algorithm_version": cls.ALGORITHM_VERSION,
            })

        # 4. Incomplete Coursework & High Lag
        incomplete_lessons = [
            l for l in lesson_progress if float(l.get("completion_percentage", 0.0)) < 30.0
        ]
        if len(incomplete_lessons) >= 4:
            signals.append({
                "signal_type": "incomplete_coursework",
                "severity": "medium",
                "title": f"Coursework Pacing Lag ({len(incomplete_lessons)} incomplete modules/lessons)",
                "evidence_data": {
                    "incomplete_count": len(incomplete_lessons),
                },
                "recommended_action": "Review student progress pace with course instructor.",
                "algorithm_version": cls.ALGORITHM_VERSION,
            })

        # 5. Weak Prerequisite Mastery
        failed_prereqs = [
            p for p in prerequisite_checks if p.get("is_ready") is False
        ]
        if failed_prereqs:
            signals.append({
                "signal_type": "weak_prerequisite_mastery",
                "severity": "high",
                "title": f"Unfulfilled Prerequisites for {len(failed_prereqs)} Advanced Modules",
                "evidence_data": {
                    "blocking_prerequisites": [p.get("prerequisite_concept_id") for p in failed_prereqs[:4]],
                },
                "recommended_action": "Require completion of foundational prerequisite concepts before continuing.",
                "algorithm_version": cls.ALGORITHM_VERSION,
            })

        # 6. Insufficient Project Evidence
        unverified_skills = [
            s for s in project_skills if s.get("verification_status") != "verified" and s.get("claimed_level") in ("proficient", "advanced", "expert")
        ]
        if len(unverified_skills) >= 4:
            signals.append({
                "signal_type": "insufficient_evidence",
                "severity": "low",
                "title": f"{len(unverified_skills)} Advanced Claimed Skills Lack Verified Evidence",
                "evidence_data": {
                    "unverified_skills_count": len(unverified_skills),
                },
                "recommended_action": "Encourage student to submit repository or demo evidence for faculty verification.",
                "algorithm_version": cls.ALGORITHM_VERSION,
            })

        # 7. Prolonged Inactivity
        if days_since_last_activity is not None and days_since_last_activity >= 14:
            severity = "urgent" if days_since_last_activity >= 21 else "high"
            signals.append({
                "signal_type": "prolonged_inactivity",
                "severity": severity,
                "title": f"No Recorded Academic Activity in {days_since_last_activity} Days",
                "evidence_data": {
                    "days_inactive": days_since_last_activity,
                },
                "recommended_action": "Advisor/mentor contact recommended to confirm enrollment status.",
                "algorithm_version": cls.ALGORITHM_VERSION,
            })

        return signals
