"""Deterministic Course Offering & Learning Analytics Engine."""

import statistics
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional


class CourseAnalyticsEngine:
    """Pure deterministic aggregation engine for Course Offerings, Assessments, Concepts, and Questions."""

    ALGORITHM_VERSION = "v1.0.0-deterministic"

    @classmethod
    def compute_assessment_metrics(
        cls,
        *,
        assessment_id: str,
        title: str,
        enrolled_count: int,
        attempts: List[Dict[str, Any]],
        questions_raw: List[Dict[str, Any]],
        responses: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculates deterministic assessment summary and question-level drill-down."""
        total_assigned = enrolled_count
        started_attempts = [a for a in attempts if a.get("status") != "not_started"]
        completed_attempts = [a for a in attempts if a.get("status") in ("evaluated", "submitted")]

        scores = [
            float(a["percentage"])
            for a in completed_attempts
            if a.get("percentage") is not None
        ]

        avg_score = round(statistics.mean(scores), 2) if scores else None
        median_score = round(statistics.median(scores), 2) if scores else None

        passed_count = sum(1 for a in completed_attempts if a.get("is_passed") is True)
        pass_rate = round(passed_count / len(completed_attempts), 4) if completed_attempts else None

        # Score distribution buckets: [0-49, 50-69, 70-84, 85-100]
        score_distribution = {
            "0_to_49": sum(1 for s in scores if s < 50.0),
            "50_to_69": sum(1 for s in scores if 50.0 <= s < 70.0),
            "70_to_84": sum(1 for s in scores if 70.0 <= s < 85.0),
            "85_to_100": sum(1 for s in scores if s >= 85.0),
        }

        pending_manual = sum(
            1 for a in attempts if a.get("status") == "under_evaluation"
        )

        # Question analytics
        questions_analyzed: List[Dict[str, Any]] = []
        for q in questions_raw:
            qid = q.get("question_id") or q.get("id")
            q_responses = [r for r in responses if r.get("question_id") == qid or r.get("question_version_id") == q.get("version_id")]
            q_attempts_count = len(q_responses)

            if q_attempts_count > 0:
                correct_count = sum(1 for r in q_responses if r.get("is_correct") is True)
                skipped_count = sum(1 for r in q_responses if not r.get("response_payload"))
                accuracy = round(correct_count / q_attempts_count, 4)
                skip_rate = round(skipped_count / q_attempts_count, 4)

                q_scores = [float(r.get("awarded_marks", 0.0)) for r in q_responses]
                q_avg_score = round(statistics.mean(q_scores), 2) if q_scores else 0.0

                review_recommended = accuracy < 0.35 or skip_rate > 0.40
                review_reason = (
                    "Unusually low accuracy (< 35%)"
                    if accuracy < 0.35
                    else ("High skip rate (> 40%)" if skip_rate > 0.40 else None)
                )
            else:
                q_avg_score = 0.0
                accuracy = 0.0
                skip_rate = 0.0
                review_recommended = False
                review_reason = None

            questions_analyzed.append({
                "question_id": qid,
                "question_title": q.get("title", f"Question {qid}"),
                "question_type": q.get("question_type", "multiple_choice"),
                "attempts_count": q_attempts_count,
                "average_score": q_avg_score,
                "accuracy_rate": accuracy,
                "skip_rate": skip_rate,
                "review_recommended": review_recommended,
                "review_reason": review_reason,
            })

        completion_rate = round(len(completed_attempts) / total_assigned, 4) if total_assigned > 0 else 0.0

        return {
            "assessment_id": assessment_id,
            "title": title,
            "total_assigned": total_assigned,
            "total_started": len(started_attempts),
            "total_completed": len(completed_attempts),
            "completion_rate": completion_rate,
            "average_score": avg_score,
            "median_score": median_score,
            "pass_rate": pass_rate,
            "score_distribution": score_distribution,
            "pending_manual_evaluations": pending_manual,
            "questions": questions_analyzed,
        }

    @classmethod
    def compute_concept_analytics(
        cls,
        *,
        concepts_raw: List[Dict[str, Any]],
        knowledge_states: List[Dict[str, Any]],
        review_states: List[Dict[str, Any]],
        prerequisite_checks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Calculates deterministic concept mastery distribution and retention risks."""
        results: List[Dict[str, Any]] = []

        for c in concepts_raw:
            cid = c.get("id") or c.get("concept_id")
            c_states = [s for s in knowledge_states if s.get("concept_id") == cid]
            mastery_vals = [float(s.get("mastery_score", 0.0)) for s in c_states]

            avg_mastery = round(statistics.mean(mastery_vals), 4) if mastery_vals else 0.0

            dist = {
                "beginner": sum(1 for m in mastery_vals if m < 0.40),
                "developing": sum(1 for m in mastery_vals if 0.40 <= m < 0.70),
                "proficient": sum(1 for m in mastery_vals if 0.70 <= m < 0.90),
                "advanced": sum(1 for m in mastery_vals if m >= 0.90),
            }

            high_retention_risk = sum(
                1 for s in c_states if float(s.get("retention_score", 1.0)) < 0.40
            )

            c_reviews = [r for r in review_states if r.get("concept_id") == cid]
            overdue_count = sum(1 for r in c_reviews if r.get("is_overdue") is True or int(r.get("days_overdue", 0)) > 0)

            c_prereqs = [p for p in prerequisite_checks if p.get("target_concept_id") == cid]
            ready_count = sum(1 for p in c_prereqs if p.get("is_ready") is True)
            prereq_rate = round(ready_count / len(c_prereqs), 4) if c_prereqs else 1.0

            results.append({
                "concept_id": cid,
                "concept_name": c.get("name") or c.get("title", f"Concept {cid}"),
                "average_mastery": avg_mastery,
                "mastery_distribution": dist,
                "high_retention_risk_count": high_retention_risk,
                "overdue_reviews_count": overdue_count,
                "prerequisite_readiness_rate": prereq_rate,
                "is_difficult": avg_mastery < 0.50 and len(mastery_vals) >= 2,
            })

        return results
