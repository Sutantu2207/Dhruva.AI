"""Pydantic V2 schemas for Domain 7: Skill Intelligence, Career Trajectories & Placement Readiness."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class SkillEvidenceRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_type: str
    source_id: str
    evidence_score: float
    evidence_weight: float
    is_verified: bool
    provenance_details: Optional[Dict[str, Any]] = None
    recorded_at: datetime


class SkillIntelligenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    skill_id: str
    skill_name: Optional[str] = None
    skill_code: Optional[str] = None
    observed_proficiency: float
    self_reported_proficiency: Optional[float] = None
    verified_proficiency: float
    confidence: float
    evidence_count: int
    verified_evidence_count: int
    assessment_evidence_count: int
    project_evidence_count: int
    course_evidence_count: int
    certification_evidence_count: int
    concept_mastery_contribution: float
    verification_status: str
    proficiency_tier: str
    algorithm_version: str
    last_evaluated_at: datetime


class SkillDetailResponse(SkillIntelligenceResponse):
    evidence_records: List[SkillEvidenceRecordResponse] = []
    associated_concepts: List[Dict[str, Any]] = []


class SkillGapResponse(BaseModel):
    skill_id: str
    skill_name: str
    importance: str
    current_proficiency: float
    required_proficiency: float
    gap_size: float
    severity: str
    reason: str


class CareerReadinessResponse(BaseModel):
    career_id: str
    career_title: str
    readiness_score: float
    fit_score: float
    confidence: float
    required_skill_coverage: float
    preferred_skill_coverage: float
    critical_skill_coverage: float
    critical_gaps_count: int
    strengths_count: int
    developing_count: int
    status: str
    explanation: Dict[str, Any]
    critical_gaps: List[SkillGapResponse] = []
    strengths: List[SkillGapResponse] = []
    developing: List[SkillGapResponse] = []
    algorithm_version: str


class CareerTrajectoryStepResponse(BaseModel):
    step_number: int
    skill_id: str
    title: str
    step_type: str
    priority: str
    status: str
    target_proficiency: float
    current_proficiency: float
    gap_size: float
    reference_course_id: Optional[str] = None
    reference_lesson_id: Optional[str] = None
    reference_concept_id: Optional[str] = None
    reference_assessment_id: Optional[str] = None
    explanation: Optional[str] = None


class CareerTrajectoryResponse(BaseModel):
    career_id: str
    career_title: str
    status: str
    total_steps: int
    completed_steps: int
    steps: List[CareerTrajectoryStepResponse] = []
    algorithm_version: str


class CareerComparisonItemResponse(BaseModel):
    career_id: str
    career_title: str
    readiness_score: float
    fit_score: float
    confidence: float
    critical_gaps_count: int
    status: str


class PlacementReadinessResponse(BaseModel):
    technical_readiness: Optional[float] = None
    assessment_readiness: Optional[float] = None
    project_evidence_score: Optional[float] = None
    communication_readiness: Optional[float] = None
    resume_readiness: Optional[float] = None
    interview_readiness: Optional[float] = None
    career_alignment: Optional[float] = None
    overall_status: str
    component_statuses: Dict[str, str] = {}
    explanation: Dict[str, Any] = {}
    algorithm_version: str


class CareerIntelligenceOverviewResponse(BaseModel):
    target_career: Optional[CareerReadinessResponse] = None
    readiness: Optional[CareerReadinessResponse] = None
    trajectory: Optional[CareerTrajectoryResponse] = None
    placement: Optional[PlacementReadinessResponse] = None
    total_skills_tracked: int = 0
    verified_skills_count: int = 0
    algorithm_version: str = "v1"
