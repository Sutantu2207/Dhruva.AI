"""Pure deterministic Placement Readiness Engine for Domain 7."""

from decimal import Decimal
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class PlacementEvaluationInput(BaseModel):
    career_readiness_score: Optional[Decimal] = None
    average_assessment_score: Optional[Decimal] = None
    verified_projects_count: int = 0
    project_score_average: Optional[Decimal] = None
    communication_score: Optional[Decimal] = None
    resume_score: Optional[Decimal] = None
    interview_score: Optional[Decimal] = None
    career_goal_match: bool = False


class PlacementReadinessResult(BaseModel):
    technical_readiness: Optional[Decimal]
    assessment_readiness: Optional[Decimal]
    project_evidence_score: Optional[Decimal]
    communication_readiness: Optional[Decimal]
    resume_readiness: Optional[Decimal]
    interview_readiness: Optional[Decimal]
    career_alignment: Optional[Decimal]
    overall_status: str  # not_yet_assessed, assessed, needs_portfolio, placement_ready
    component_statuses: Dict[str, str]
    explanation: Dict[str, Any]
    algorithm_version: str


class PlacementReadinessEngine:
    """Evaluates multi-component placement readiness without fabricating unobserved metrics."""

    def __init__(self, algorithm_version: str = "v1"):
        self.algorithm_version = algorithm_version

    def evaluate_placement_readiness(
        self,
        data: PlacementEvaluationInput,
    ) -> PlacementReadinessResult:
        """Evaluates readiness components honestly. Missing components are labeled 'not_assessed'."""
        comp_statuses: Dict[str, str] = {}

        # 1. Technical readiness
        tech_val = None
        if data.career_readiness_score is not None:
            tech_val = round(max(Decimal("0.0"), min(Decimal("1.0"), data.career_readiness_score)), 4)
            comp_statuses["technical"] = "assessed"
        else:
            comp_statuses["technical"] = "not_assessed"

        # 2. Assessment readiness
        asst_val = None
        if data.average_assessment_score is not None:
            asst_val = round(max(Decimal("0.0"), min(Decimal("1.0"), data.average_assessment_score)), 4)
            comp_statuses["assessment"] = "assessed"
        else:
            comp_statuses["assessment"] = "not_assessed"

        # 3. Project evidence
        proj_val = None
        if data.verified_projects_count > 0:
            base_score = data.project_score_average or Decimal("0.7000")
            proj_val = round(max(Decimal("0.0"), min(Decimal("1.0"), base_score)), 4)
            comp_statuses["projects"] = "assessed"
        else:
            comp_statuses["projects"] = "not_assessed"

        # 4. Soft skills / Communication
        comm_val = None
        if data.communication_score is not None:
            comm_val = round(max(Decimal("0.0"), min(Decimal("1.0"), data.communication_score)), 4)
            comp_statuses["communication"] = "assessed"
        else:
            comp_statuses["communication"] = "not_assessed"

        # 5. Resume
        resume_val = None
        if data.resume_score is not None:
            resume_val = round(max(Decimal("0.0"), min(Decimal("1.0"), data.resume_score)), 4)
            comp_statuses["resume"] = "assessed"
        else:
            comp_statuses["resume"] = "not_assessed"

        # 6. Interview
        interview_val = None
        if data.interview_score is not None:
            interview_val = round(max(Decimal("0.0"), min(Decimal("1.0"), data.interview_score)), 4)
            comp_statuses["interview"] = "assessed"
        else:
            comp_statuses["interview"] = "not_assessed"

        # 7. Career alignment
        alignment_val = Decimal("1.0000") if data.career_goal_match else Decimal("0.4000")
        comp_statuses["career_alignment"] = "assessed"

        # Determine overall status
        assessed_components = [k for k, v in comp_statuses.items() if v == "assessed"]
        
        # Invariant: If critical employment components (interview/resume) are missing, status cannot be placement_ready
        if len(assessed_components) < 3:
            overall_status = "not_yet_assessed"
            explanation_summary = "Fewer than 3 competency components evaluated; profile is still in development."
        elif proj_val is None or proj_val < Decimal("0.5000"):
            overall_status = "needs_portfolio"
            explanation_summary = "Technical evaluations in progress, but verified project portfolio artifacts are required."
        elif (
            tech_val is not None
            and tech_val >= Decimal("0.7500")
            and asst_val is not None
            and asst_val >= Decimal("0.7000")
        ):
            overall_status = "placement_ready"
            explanation_summary = "Technical and assessment benchmarks met for campus recruitment readiness."
        else:
            overall_status = "assessed"
            explanation_summary = "Readiness assessed; continue progressing on identified gap milestones."

        return PlacementReadinessResult(
            technical_readiness=tech_val,
            assessment_readiness=asst_val,
            project_evidence_score=proj_val,
            communication_readiness=comm_val,
            resume_readiness=resume_val,
            interview_readiness=interview_val,
            career_alignment=alignment_val,
            overall_status=overall_status,
            component_statuses=comp_statuses,
            explanation={
                "overall_status": overall_status,
                "summary": explanation_summary,
                "assessed_components_count": len(assessed_components),
                "unassessed_components": [k for k, v in comp_statuses.items() if v == "not_assessed"],
            },
            algorithm_version=self.algorithm_version,
        )
