"""Deterministic Departmental Analytics Engine for HOD oversight and Institutional Comparisons."""

import statistics
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional


class DepartmentAnalyticsEngine:
    """Pure deterministic aggregation engine for Departmental intelligence and Academic Trends."""

    ALGORITHM_VERSION = "v1.0.0-deterministic"
    MINIMUM_COHORT_SUPPRESSION_THRESHOLD = 3

    @classmethod
    def aggregate_department_metrics(
        cls,
        *,
        department_id: str,
        department_name: str,
        department_code: str,
        total_programs: int,
        total_courses: int,
        total_offerings: int,
        total_faculty: int,
        total_students: int,
        course_completions: List[float],
        assessment_scores: List[float],
        concept_mastery_scores: List[float],
        career_readiness_scores: List[float],
        verified_projects_count: int,
        signals_by_severity: Dict[str, int],
        difficult_concepts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculates deterministic HOD department overview."""
        avg_completion = round(statistics.mean(course_completions), 4) if course_completions else 0.0
        avg_assessment = round(statistics.mean(assessment_scores), 2) if assessment_scores else None
        avg_mastery = round(statistics.mean(concept_mastery_scores), 4) if concept_mastery_scores else None
        avg_career = round(statistics.mean(career_readiness_scores), 4) if career_readiness_scores else None

        active_signals_count = sum(signals_by_severity.values())

        return {
            "department_id": department_id,
            "department_name": department_name,
            "department_code": department_code,
            "total_programs": total_programs,
            "total_courses": total_courses,
            "total_offerings": total_offerings,
            "total_faculty": total_faculty,
            "total_students": total_students,
            "average_course_completion": avg_completion,
            "average_assessment_score": avg_assessment,
            "concept_mastery_average": avg_mastery,
            "career_readiness_average": avg_career,
            "verified_projects_count": verified_projects_count,
            "active_intervention_signals_count": active_signals_count,
            "interventions_by_severity": signals_by_severity,
            "top_difficult_concepts": difficult_concepts[:5],
            "algorithm_version": cls.ALGORITHM_VERSION,
            "calculated_at": datetime.now(timezone.utc),
        }

    @classmethod
    def compare_departments(
        cls,
        *,
        department_summaries: List[Dict[str, Any]],
        min_cohort_size: int = MINIMUM_COHORT_SUPPRESSION_THRESHOLD,
    ) -> List[Dict[str, Any]]:
        """Compares departments with strict small-cohort suppression to protect individual student privacy."""
        comparisons: List[Dict[str, Any]] = []

        for d in department_summaries:
            student_count = d.get("total_students", 0)
            is_suppressed = student_count < min_cohort_size

            if is_suppressed:
                comparisons.append({
                    "department_id": d["department_id"],
                    "department_name": d["department_name"],
                    "department_code": d["department_code"],
                    "student_count": student_count,
                    "is_suppressed": True,
                    "completion_rate": None,
                    "average_score": None,
                    "concept_mastery": None,
                    "career_readiness": None,
                    "active_interventions": None,
                })
            else:
                comparisons.append({
                    "department_id": d["department_id"],
                    "department_name": d["department_name"],
                    "department_code": d["department_code"],
                    "student_count": student_count,
                    "is_suppressed": False,
                    "completion_rate": d.get("average_course_completion"),
                    "average_score": d.get("average_assessment_score"),
                    "concept_mastery": d.get("concept_mastery_average"),
                    "career_readiness": d.get("career_readiness_average"),
                    "active_interventions": d.get("active_intervention_signals_count", 0),
                })

        return comparisons
