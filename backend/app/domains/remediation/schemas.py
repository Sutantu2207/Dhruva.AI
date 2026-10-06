"""Pydantic schemas for Domain 10: Adaptive Remediation."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


# =========================================================================
# Plan Step Schemas
# =========================================================================

class RemediationPlanStepBase(BaseModel):
    sequence_order: int
    step_type: str
    concept_id: Optional[str] = None
    lesson_id: Optional[str] = None
    resource_id: Optional[str] = None
    assessment_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    required: bool = True
    scaffold_level: int = 1


class RemediationPlanStepResponse(RemediationPlanStepBase):
    id: str
    remediation_plan_id: str
    completion_status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result_summary: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Remediation Diagnosis Schemas
# =========================================================================

class RemediationDiagnosisResponse(BaseModel):
    id: str
    remediation_plan_id: str
    concept_id: str
    evidence_count: int
    mastery_before: Optional[Decimal] = None
    confidence_before: Decimal
    retention_before: Decimal
    prerequisite_readiness: Optional[Decimal] = None
    failure_count: int
    overdue_review_count: int
    recent_performance: Optional[Decimal] = None
    diagnosis_category: str
    diagnosis_reason: str
    explanation_payload: Dict[str, Any]
    algorithm_version: str
    calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Remediation Attempt Schemas
# =========================================================================

class CompleteStepPayload(BaseModel):
    score: Optional[Decimal] = Field(None, ge=0, le=100)
    completion_percentage: Decimal = Field(Decimal("100.00"), ge=0, le=100)
    evidence_generated: Dict[str, Any] = Field(default_factory=dict)


class RemediationAttemptResponse(BaseModel):
    id: str
    remediation_plan_step_id: str
    student_profile_id: str
    attempt_number: int
    started_at: datetime
    submitted_at: Optional[datetime] = None
    score: Optional[Decimal] = None
    completion_percentage: Decimal
    outcome: str
    evidence_generated: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Remediation Outcome Schemas
# =========================================================================

class RemediationOutcomeResponse(BaseModel):
    id: str
    remediation_plan_id: str
    concept_id: str
    mastery_before: Optional[Decimal] = None
    confidence_before: Decimal
    retention_before: Decimal
    assessment_score_before: Optional[Decimal] = None
    mastery_after: Optional[Decimal] = None
    confidence_after: Decimal
    retention_after: Decimal
    assessment_score_after: Optional[Decimal] = None
    improvement_delta: Decimal
    outcome_status: str
    closure_decision: str
    closure_reason: str
    algorithm_version: str
    measured_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Remediation Plan Schemas
# =========================================================================

class RemediationPlanResponse(BaseModel):
    id: str
    student_profile_id: str
    originating_signal_id: Optional[str] = None
    originating_intervention_id: Optional[str] = None
    target_concept_id: str
    target_skill_id: Optional[str] = None
    target_course_offering_id: Optional[str] = None
    diagnosis_type: str
    diagnosis_reason: str
    priority_score: Decimal
    status: str
    idempotency_key: str
    algorithm_version: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    faculty_override_reason: Optional[str] = None
    faculty_reviewer_id: Optional[str] = None

    steps: List[RemediationPlanStepResponse] = []
    diagnoses: List[RemediationDiagnosisResponse] = []
    outcomes: List[RemediationOutcomeResponse] = []

    # Enriched context
    target_concept_name: Optional[str] = None
    student_name: Optional[str] = None
    course_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class GenerateRemediationPlanPayload(BaseModel):
    signal_id: str


class ModifyRemediationPlanPayload(BaseModel):
    reason: str
    added_steps: Optional[List[RemediationPlanStepBase]] = None
    remove_step_ids: Optional[List[str]] = None


class FacultyOverridePayload(BaseModel):
    reason: str


# =========================================================================
# Analytics, Content Gaps & Accreditation Schemas
# =========================================================================

class InstitutionalRemediationAnalytics(BaseModel):
    plans_created: int
    plans_completed: int
    completion_rate: Decimal
    improvement_rate: Decimal
    partial_improvement_rate: Decimal
    no_significant_change_rate: Decimal
    regression_rate: Decimal
    average_mastery_improvement: Decimal
    prerequisite_bottlenecks: List[Dict[str, Any]]
    concepts_highest_demand: List[Dict[str, Any]]
    courses_highest_demand: List[Dict[str, Any]]
    content_availability_gaps: int
    closure_rate: Decimal
    algorithm_version: str


class DepartmentRemediationAnalytics(BaseModel):
    department_id: str
    department_name: str
    plans_created: int
    plans_completed: int
    completion_rate: Decimal
    average_mastery_improvement: Decimal
    courses_demand: List[Dict[str, Any]]
    concepts_demand: List[Dict[str, Any]]
    content_gaps_count: int


class ContentGapResponse(BaseModel):
    id: str
    institution_id: str
    concept_id: str
    concept_name: Optional[str] = None
    course_id: Optional[str] = None
    course_name: Optional[str] = None
    demand_count: int
    gap_type: str
    status: str
    detected_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AccreditationEvidenceRequest(BaseModel):
    framework: str = Field(..., json_schema_extra={"example": "NAAC"})  # NAAC, NBA
    criterion: str = Field(..., json_schema_extra={"example": "2.2.1"})


class AccreditationEvidenceResponse(BaseModel):
    id: str
    institution_id: str
    framework: str
    criterion: str
    metric_code: str
    metric_payload: Dict[str, Any]
    source_domain: str
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)
