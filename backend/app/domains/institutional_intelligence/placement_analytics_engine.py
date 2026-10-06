"""Deterministic Placement & Employability Intelligence Engine."""

import statistics
from collections import Counter
from typing import List, Dict, Any, Optional


class PlacementAnalyticsEngine:
    """Pure deterministic aggregation engine for institution-wide employability and placement analytics."""

    ALGORITHM_VERSION = "v1.0.0-deterministic"

    @classmethod
    def aggregate_placement_intelligence(
        cls,
        *,
        total_students: int,
        career_goals: List[Dict[str, Any]],
        career_readiness_states: List[Dict[str, Any]],
        placement_states: List[Dict[str, Any]],
        student_verified_projects: Dict[str, int],  # student_profile_id -> verified_project_count
        portfolio_snapshots: List[Dict[str, Any]],
        skill_gaps: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Synthesizes deterministic placement metrics without speculative employment predictions."""
        # 1. Career target distribution
        target_counts = Counter(g.get("career_title", "Unspecified") for g in career_goals)
        total_goals = len(career_goals)
        career_distribution = [
            {
                "career_title": title,
                "student_count": count,
                "percentage": round(count / total_goals, 4) if total_goals > 0 else 0.0,
            }
            for title, count in target_counts.most_common(8)
        ]

        # 2. Career readiness tiers & average
        readiness_scores = [
            float(r["overall_readiness_percentage"])
            for r in career_readiness_states
            if r.get("overall_readiness_percentage") is not None
        ]
        avg_readiness = round(statistics.mean(readiness_scores), 2) if readiness_scores else None

        readiness_tiers = {
            "ready": sum(1 for s in readiness_scores if s >= 75.0),
            "near_ready": sum(1 for s in readiness_scores if 50.0 <= s < 75.0),
            "developing": sum(1 for s in readiness_scores if s < 50.0),
            "unassessed": max(0, total_students - len(readiness_scores)),
        }

        # 3. Placement readiness states distribution
        placement_dist = Counter(
            p.get("readiness_tier", "unassessed") for p in placement_states
        )
        placement_distribution = {
            "ready": placement_dist.get("ready", 0),
            "near_ready": placement_dist.get("near_ready", 0),
            "developing": placement_dist.get("developing", 0),
            "unassessed": total_students - len(placement_states),
        }

        # 4. Verified project coverage rate
        students_with_verified_projects = sum(
            1 for count in student_verified_projects.values() if count > 0
        )
        verified_project_coverage = (
            round(students_with_verified_projects / total_students, 4) if total_students > 0 else 0.0
        )

        # 5. Portfolio health average
        portfolio_scores = [
            float(p["overall_health_score"])
            for p in portfolio_snapshots
            if p.get("overall_health_score") is not None
        ]
        avg_portfolio_health = round(statistics.mean(portfolio_scores), 2) if portfolio_scores else None

        # 6. Top systemic skill gaps
        gap_counter = Counter(g.get("skill_name") for g in skill_gaps if g.get("skill_name"))
        top_gaps = [
            {"skill_name": name, "impacted_students_count": count}
            for name, count in gap_counter.most_common(10)
        ]

        return {
            "evaluated_students_count": len(readiness_scores),
            "career_target_distribution": career_distribution,
            "career_readiness_tiers": readiness_tiers,
            "average_career_readiness": avg_readiness,
            "top_systemic_skill_gaps": top_gaps,
            "verified_project_coverage_rate": verified_project_coverage,
            "portfolio_health_average": avg_portfolio_health,
            "placement_readiness_distribution": placement_distribution,
            "algorithm_version": cls.ALGORITHM_VERSION,
        }
