"""Deterministic Prerequisite Readiness Engine."""

from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple


class PrerequisiteReadinessEngine:
    """Evaluates student readiness for target concepts based on directed prerequisite relationships."""

    @staticmethod
    def evaluate_readiness(
        target_concept_id: str,
        prerequisite_graph: Dict[str, List[str]],  # concept_id -> list of prerequisite_concept_ids
        student_masteries: Dict[str, Optional[Decimal]],  # concept_id -> mastery decimal (or None)
    ) -> Tuple[Optional[Decimal], str]:
        """Calculates readiness score [0.0000, 1.0000] and health status.
        
        Returns:
            Tuple of (readiness_score, health_status)
            where health_status is one of: 'healthy', 'partial', 'weak', 'unknown'
        """
        direct_prereqs = prerequisite_graph.get(target_concept_id, [])
        if not direct_prereqs:
            # Concepts with no prerequisites are inherently healthy / ready
            return Decimal("1.0000"), "healthy"

        # Check for cycles defensively
        all_prereqs = PrerequisiteReadinessEngine._get_all_ancestor_prereqs(
            target_concept_id, prerequisite_graph
        )

        scores: List[float] = []
        has_unknown = False

        for pid in direct_prereqs:
            m = student_masteries.get(pid)
            if m is None:
                has_unknown = True
            else:
                scores.append(float(m))

        if not scores:
            return None, "unknown"

        # Direct readiness: average of observed direct prerequisites
        avg_score = sum(scores) / len(scores)
        readiness_score = Decimal(str(round(avg_score, 4)))

        # Categorize health
        if avg_score >= 0.70:
            health = "healthy"
        elif avg_score >= 0.40:
            health = "partial"
        else:
            health = "weak"

        if has_unknown and health == "healthy":
            health = "partial"

        return readiness_score, health

    @staticmethod
    def _get_all_ancestor_prereqs(
        start_concept_id: str,
        graph: Dict[str, List[str]],
    ) -> Set[str]:
        """Collects all upstream prerequisites using DFS with cycle prevention."""
        visited: Set[str] = set()

        def dfs(current: str):
            for prereq in graph.get(current, []):
                if prereq not in visited and prereq != start_concept_id:
                    visited.add(prereq)
                    dfs(prereq)

        dfs(start_concept_id)
        return visited
