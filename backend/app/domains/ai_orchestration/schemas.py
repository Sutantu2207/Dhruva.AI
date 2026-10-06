"""Schemas for Controlled AI Orchestration."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class AIExplanationRequest(BaseModel):
    concept_id: str
    concept_name: str
    difficulty_level: str = "intermediate"
    student_weakness_context: Optional[str] = None
    scoped_metadata: Dict[str, Any] = Field(default_factory=dict)


class AIExplanationResponse(BaseModel):
    concept_id: str
    explanation: str
    analogies: list[str]
    practice_suggestion: str
    model_used: str
    token_usage: Dict[str, int]
