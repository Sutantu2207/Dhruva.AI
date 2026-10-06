"""Deterministic Prerequisite Path Engine (Domain 10).

Traverses the canonical ConceptPrerequisite DAG recursively to:
- Trace full prerequisite chain
- Detect cycles and avoid infinite loops
- Determine prerequisite readiness & identify blocking concepts
- Identify the first recommended remediation concept
"""

from typing import Dict, List, Set, Optional, Tuple, Any
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.content.models import Concept, ConceptPrerequisite
from app.domains.mastery.models import StudentConceptKnowledgeState
from app.domains.remediation.config import (
    MAX_PREREQUISITE_TRAVERSAL_DEPTH,
    PREREQUISITE_READINESS_THRESHOLD,
    ALGORITHM_VERSION,
)


class PrerequisitePathEngine:
    """Pure and database-backed deterministic prerequisite DAG traversal engine."""

    @staticmethod
    def detect_cycle_in_graph(
        adj_list: Dict[str, List[str]], start_node: str
    ) -> bool:
        """Pure graph cycle detection using depth-first search with recursion stack."""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in adj_list.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        return dfs(start_node)

    @staticmethod
    async def get_prerequisite_chain(
        db: AsyncSession,
        target_concept_id: str,
        student_profile_id: Optional[str] = None,
        max_depth: int = MAX_PREREQUISITE_TRAVERSAL_DEPTH,
    ) -> Dict[str, Any]:
        """Traverse prerequisite DAG from target_concept_id upwards to root prerequisites.
        
        Returns:
            - chain: Ordered list of prerequisite concept metadata from furthest root to target
            - blocking_prerequisites: Concepts with mastery < threshold
            - is_ready: True if no blocking prerequisites exist
            - root_remediation_concept: First concept in chain requiring remediation
            - has_cycle: Boolean indicating whether a cycle was detected and severed
        """
        visited_nodes: Set[str] = set()
        chain: List[Dict[str, Any]] = []
        blocking: List[Dict[str, Any]] = []
        has_cycle = False

        # Load all relevant concepts and prerequisites efficiently
        queue = [(target_concept_id, 0)]
        adjacency: Dict[str, List[str]] = {}
        all_concept_ids: Set[str] = {target_concept_id}

        while queue:
            curr_id, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            # Query direct prerequisites
            stmt = select(ConceptPrerequisite).where(ConceptPrerequisite.concept_id == curr_id)
            res = await db.execute(stmt)
            prereqs = res.scalars().all()

            adjacency[curr_id] = []
            for p in prereqs:
                prereq_id = p.prerequisite_concept_id
                all_concept_ids.add(prereq_id)
                adjacency[curr_id].append(prereq_id)

                if prereq_id in visited_nodes:
                    has_cycle = True
                    continue

                visited_nodes.add(prereq_id)
                queue.append((prereq_id, depth + 1))

        # Fetch knowledge states for all concepts in the traversed subgraph if student_profile_id is provided
        knowledge_map: Dict[str, StudentConceptKnowledgeState] = {}
        if student_profile_id and all_concept_ids:
            k_stmt = select(StudentConceptKnowledgeState).where(
                StudentConceptKnowledgeState.student_profile_id == student_profile_id,
                StudentConceptKnowledgeState.concept_id.in_(all_concept_ids),
            )
            k_res = await db.execute(k_stmt)
            for k in k_res.scalars().all():
                knowledge_map[k.concept_id] = k

        # Fetch concept names and details
        c_stmt = select(Concept).where(Concept.id.in_(all_concept_ids))
        c_res = await db.execute(c_stmt)
        concept_map = {c.id: c for c in c_res.scalars().all()}

        # Topologically sort / linearize prerequisite path (deepest prerequisites first)
        linearized_ids = []
        visited_topo: Set[str] = set()

        def topo_sort(cid: str):
            visited_topo.add(cid)
            for p_id in adjacency.get(cid, []):
                if p_id not in visited_topo:
                    topo_sort(p_id)
            if cid != target_concept_id:
                linearized_ids.append(cid)

        topo_sort(target_concept_id)

        first_unmastered_prereq: Optional[Dict[str, Any]] = None

        for cid in linearized_ids:
            c = concept_map.get(cid)
            if not c:
                continue

            k_state = knowledge_map.get(cid)
            mastery = Decimal(str(k_state.current_mastery)) if (k_state and k_state.current_mastery is not None) else Decimal("0.0")
            confidence = Decimal(str(k_state.confidence)) if k_state else Decimal("0.0")

            node_info = {
                "concept_id": cid,
                "name": c.name,
                "slug": c.slug,
                "mastery": float(mastery),
                "confidence": float(confidence),
                "is_blocking": mastery < PREREQUISITE_READINESS_THRESHOLD,
            }
            chain.append(node_info)

            if node_info["is_blocking"]:
                blocking.append(node_info)
                if first_unmastered_prereq is None:
                    first_unmastered_prereq = node_info

        is_ready = len(blocking) == 0

        return {
            "target_concept_id": target_concept_id,
            "chain": chain,
            "blocking_prerequisites": blocking,
            "is_ready": is_ready,
            "first_recommended_concept": first_unmastered_prereq or (
                {"concept_id": target_concept_id, "name": concept_map[target_concept_id].name if target_concept_id in concept_map else "Target Concept"}
            ),
            "has_cycle": has_cycle,
            "algorithm_version": ALGORITHM_VERSION,
        }
