"""Pydantic V2 Schemas for Domain 6 Knowledge State, Mastery & Spaced Repetition."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ConceptKnowledgeStateResponse(BaseModel):
    """Authoritative student concept knowledge state representation."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    concept_id: str
    concept_name: Optional[str] = None
    concept_slug: Optional[str] = None
    current_mastery: Optional[float] = None  # None indicates unobserved / insufficient evidence
    confidence: float
    retention_estimate: float
    state: str  # unknown, introduced, developing, proficient, mastered, at_risk
    trend: str  # strongly_improving, improving, stable, declining, strongly_declining, insufficient_data
    evidence_count: int
    first_evidence_at: Optional[datetime] = None
    last_evidence_at: Optional[datetime] = None
    last_successful_evidence_at: Optional[datetime] = None
    last_failed_evidence_at: Optional[datetime] = None
    prerequisite_readiness: Optional[float] = None
    prerequisite_health: str
    algorithm_version: str
    updated_at: datetime


class KnowledgeStateHistoryResponse(BaseModel):
    """Historical audit snapshot entry for a knowledge state recalculation."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    concept_id: str
    previous_mastery: Optional[float] = None
    new_mastery: Optional[float] = None
    change: Optional[float] = None
    confidence: float
    retention_estimate: float
    state: str
    trend: str
    trigger: str
    algorithm_version: str
    timestamp: datetime


class ConceptReviewStateResponse(BaseModel):
    """Active Spaced Repetition schedule item."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    concept_id: str
    concept_name: Optional[str] = None
    repetition: int
    ease_factor: float
    interval_days: int
    last_reviewed_at: Optional[datetime] = None
    next_review_at: datetime
    last_quality: Optional[int] = None
    review_status: str  # due, upcoming, overdue, completed
    retention_estimate: Optional[float] = None
    algorithm_version: str


class ConceptReviewCompletionPayload(BaseModel):
    """Student submission payload upon completing a spaced repetition recall trial."""
    quality: int = Field(ge=0, le=5, description="Recall rating: 0 (blackout) to 5 (flawless)")
    duration_seconds: Optional[int] = Field(default=None, ge=1, le=7200)
    trigger: Optional[str] = Field(default="recall_session")


class ConceptReviewHistoryResponse(BaseModel):
    """Audit log entry for a completed review."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    concept_id: str
    quality: int
    previous_interval: int
    new_interval: int
    previous_ease: float
    new_ease: float
    duration_seconds: Optional[int] = None
    trigger: str
    algorithm_version: str
    reviewed_at: datetime


class LearningPriorityResponse(BaseModel):
    """Single concept learning priority item."""
    concept_id: str
    concept_name: str
    priority_score: float
    reason_codes: List[str]
    mastery_gap: float
    retention_risk: float
    prerequisite_readiness: float
    recommended_task_type: str
    reference_lesson_id: Optional[str] = None
    reference_assessment_id: Optional[str] = None


class DailyMissionTaskResponse(BaseModel):
    """Structured mission task in daily study plan."""
    task_id: str
    task_type: str
    title: str
    concept_id: str
    concept_name: str
    priority_score: float
    reason_codes: List[str]
    reference_id: Optional[str] = None
    estimated_minutes: int = 15


class DailyMissionResponse(BaseModel):
    """Container for the student's daily recommended study mission."""
    date: str
    tasks: List[DailyMissionTaskResponse]
    total_estimated_minutes: int


class ConceptPrerequisiteItemResponse(BaseModel):
    """Directed prerequisite relationship detail."""
    concept_id: str
    concept_name: str
    relationship_type: str
    mastery: Optional[float] = None
    state: str = "unknown"


class ConceptDetailResponse(BaseModel):
    """Comprehensive detail view for a specific canonical concept."""
    concept_id: str
    name: str
    slug: str
    description: Optional[str] = None
    difficulty: str
    knowledge_state: Optional[ConceptKnowledgeStateResponse] = None
    review_state: Optional[ConceptReviewStateResponse] = None
    prerequisites: List[ConceptPrerequisiteItemResponse] = Field(default_factory=list)
    prerequisite_readiness: Optional[float] = None
    prerequisite_health: str = "healthy"
    evidence_history: List[Dict[str, Any]] = Field(default_factory=list)
    mastery_history: List[KnowledgeStateHistoryResponse] = Field(default_factory=list)
    explanation: Dict[str, Any] = Field(default_factory=dict)


class StudentKnowledgeSummaryResponse(BaseModel):
    """Aggregate overview of a student's holistic knowledge state."""
    student_profile_id: str
    student_name: str
    total_concepts_tracked: int
    mastered_count: int
    proficient_count: int
    developing_count: int
    introduced_count: int
    at_risk_count: int
    due_reviews_count: int
    average_mastery: Optional[float] = None
    average_retention: float
