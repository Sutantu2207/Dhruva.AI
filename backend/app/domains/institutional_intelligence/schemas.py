"""Pydantic schemas for Institutional Analytics, Grading Workflows & Departmental Intelligence."""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# -------------------------------------------------------------------------
# 1. Early Intervention Signal Schemas
# -------------------------------------------------------------------------

class InterventionSignalResponse(BaseModel):
    id: str
    institution_id: str
    student_profile_id: str
    student_name: Optional[str] = None
    enrollment_number: Optional[str] = None
    course_offering_id: Optional[str] = None
    course_code: Optional[str] = None
    course_title: Optional[str] = None
    signal_type: str
    severity: str
    title: str
    evidence_data: Dict[str, Any]
    recommended_action: str
    status: str
    detected_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by_user_id: Optional[str] = None
    dismiss_reason: Optional[str] = None
    intervention_id: Optional[str] = None
    algorithm_version: str

    model_config = {"from_attributes": True}


class AcknowledgeSignalPayload(BaseModel):
    notes: Optional[str] = None


class DismissSignalPayload(BaseModel):
    reason: str = Field(..., min_length=3, max_length=500)


class ConvertSignalToInterventionPayload(BaseModel):
    category: str = "academic_support"
    priority: str = "high"
    action_plan: Optional[str] = None
    follow_up_date: Optional[date] = None


# -------------------------------------------------------------------------
# 2. Grading Queue & Workflow Schemas
# -------------------------------------------------------------------------

class GradingQueueItem(BaseModel):
    item_id: str
    item_type: str  # manual_question, project_review, evidence_verification
    priority: str  # low, medium, high, urgent
    title: str
    student_profile_id: str
    student_name: str
    enrollment_number: Optional[str] = None
    course_offering_id: Optional[str] = None
    course_code: Optional[str] = None
    course_title: Optional[str] = None
    submitted_at: datetime
    status: str  # pending, in_progress, returned, completed
    metadata_json: Optional[Dict[str, Any]] = None


class ManualGradingSubmission(BaseModel):
    awarded_marks: Decimal
    feedback: Optional[str] = None
    rubric_scores: Optional[Dict[str, Decimal]] = None


class RegradeSubmission(BaseModel):
    new_marks: Decimal
    reason: str = Field(..., min_length=5, max_length=1000)


# -------------------------------------------------------------------------
# 3. Course Offering Analytics Schemas
# -------------------------------------------------------------------------

class ConceptAnalyticsItem(BaseModel):
    concept_id: str
    concept_name: str
    average_mastery: float
    mastery_distribution: Dict[str, int]  # beginner, developing, proficient, advanced
    high_retention_risk_count: int
    overdue_reviews_count: int
    prerequisite_readiness_rate: float
    is_difficult: bool


class QuestionAnalyticsItem(BaseModel):
    question_id: str
    question_title: str
    question_type: str
    attempts_count: int
    average_score: float
    accuracy_rate: float
    skip_rate: float
    review_recommended: bool
    review_reason: Optional[str] = None


class AssessmentAnalyticsSummary(BaseModel):
    assessment_id: str
    title: str
    total_assigned: int
    total_started: int
    total_completed: int
    completion_rate: float
    average_score: Optional[float] = None
    median_score: Optional[float] = None
    pass_rate: Optional[float] = None
    score_distribution: Dict[str, int]
    pending_manual_evaluations: int
    questions: List[QuestionAnalyticsItem] = []


class CourseOfferingAnalyticsResponse(BaseModel):
    offering_id: str
    course_id: str
    course_code: str
    course_title: str
    section_name: str
    enrolled_count: int
    active_learners_count: int
    average_lesson_progress: float
    completion_rate: float
    assessments_summary: List[AssessmentAnalyticsSummary]
    concepts_analytics: List[ConceptAnalyticsItem]
    difficult_concepts: List[str]
    active_intervention_signals_count: int
    project_evidence_count: int
    algorithm_version: str
    calculated_at: datetime


# -------------------------------------------------------------------------
# 4. Faculty Dashboard Overview
# -------------------------------------------------------------------------

class FacultyDashboardAnalytics(BaseModel):
    assigned_offerings_count: int
    total_enrolled_students: int
    pending_grading_count: int
    active_intervention_signals_count: int
    recent_assessments_count: int
    average_cohort_completion: float
    offerings: List[Dict[str, Any]]
    urgent_signals: List[InterventionSignalResponse]


# -------------------------------------------------------------------------
# 5. Department Analytics (HOD) Schemas
# -------------------------------------------------------------------------

class DepartmentAnalyticsResponse(BaseModel):
    department_id: str
    department_name: str
    department_code: str
    total_programs: int
    total_courses: int
    total_offerings: int
    total_faculty: int
    total_students: int
    average_course_completion: float
    average_assessment_score: Optional[float] = None
    concept_mastery_average: Optional[float] = None
    career_readiness_average: Optional[float] = None
    verified_projects_count: int
    active_intervention_signals_count: int
    interventions_by_severity: Dict[str, int]
    top_difficult_concepts: List[Dict[str, Any]]
    algorithm_version: str
    calculated_at: datetime


class DepartmentComparisonItem(BaseModel):
    department_id: str
    department_name: str
    department_code: str
    student_count: int
    is_suppressed: bool  # True if student_count < minimum_cohort_threshold
    completion_rate: Optional[float] = None
    average_score: Optional[float] = None
    concept_mastery: Optional[float] = None
    career_readiness: Optional[float] = None
    active_interventions: Optional[int] = None


class DepartmentComparisonResponse(BaseModel):
    institution_id: str
    minimum_cohort_size: int
    departments: List[DepartmentComparisonItem]
    algorithm_version: str
    calculated_at: datetime


# -------------------------------------------------------------------------
# 6. Placement Officer Analytics Schemas
# -------------------------------------------------------------------------

class PlacementOfficerAnalyticsResponse(BaseModel):
    institution_id: str
    evaluated_students_count: int
    career_target_distribution: List[Dict[str, Any]]
    career_readiness_tiers: Dict[str, int]  # ready, near_ready, developing, unassessed
    average_career_readiness: Optional[float] = None
    top_systemic_skill_gaps: List[Dict[str, Any]]
    verified_project_coverage_rate: float
    portfolio_health_average: Optional[float] = None
    placement_readiness_distribution: Dict[str, int]
    algorithm_version: str
    calculated_at: datetime


# -------------------------------------------------------------------------
# 7. Cohort Drill-Down & Reports
# -------------------------------------------------------------------------

class CohortLearningAnalyticsResponse(BaseModel):
    batch_id: str
    batch_name: str
    program_id: str
    program_name: str
    student_count: int
    active_students_count: int
    average_completion: float
    average_assessment_performance: Optional[float] = None
    average_concept_mastery: Optional[float] = None
    average_career_readiness: Optional[float] = None
    interventions_count: int
    algorithm_version: str
    calculated_at: datetime
