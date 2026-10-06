"""Pydantic V2 Schemas for Domain 11 AI Orchestration."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


# =========================================================================
# Conversational Schemas
# =========================================================================

class AICitationResponse(BaseModel):
    id: str
    source_type: str
    source_id: str
    title: str
    chunk_id: Optional[str] = None
    relevance_score: float

    model_config = ConfigDict(from_attributes=True)


class AIToolInvocationResponse(BaseModel):
    id: str
    tool_name: str
    arguments_hash: str
    status: str
    latency_ms: int

    model_config = ConfigDict(from_attributes=True)


class AIMessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    status: str
    created_at: datetime
    citations: List[AICitationResponse] = []
    tool_invocations: List[AIToolInvocationResponse] = []

    model_config = ConfigDict(from_attributes=True)


class AIConversationResponse(BaseModel):
    id: str
    user_id: str
    institution_id: Optional[str] = None
    scope: str
    title: str
    status: str
    current_mode: str
    created_at: datetime
    updated_at: datetime
    last_activity_at: datetime
    messages: List[AIMessageResponse] = []

    model_config = ConfigDict(from_attributes=True)


class CreateConversationPayload(BaseModel):
    title: Optional[str] = "New Conversation"
    current_mode: str = "EXPLAIN"


class SendMessagePayload(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
    current_mode: Optional[str] = None
    context_concept_id: Optional[str] = None
    context_course_offering_id: Optional[str] = None


class AIFeedbackPayload(BaseModel):
    rating: str = Field(..., pattern="^(thumbs_up|thumbs_down)$")
    reason: Optional[str] = None
    comment: Optional[str] = None


# =========================================================================
# Structured AI Generation Schemas (Faculty Copilot)
# =========================================================================

class QuestionDraftSchema(BaseModel):
    prompt: str
    difficulty: str
    target_concept_name: str
    options: List[Dict[str, Any]]
    explanation: str
    label: str = "AI DRAFT"


class RubricDraftSchema(BaseModel):
    title: str
    criteria: List[Dict[str, Any]]
    max_score: float
    label: str = "AI DRAFT"


class AIUsageMetricsResponse(BaseModel):
    total_conversations: int
    total_messages: int
    total_input_tokens: int
    total_output_tokens: int
    estimated_total_cost: Decimal
    audit_events_count: int
