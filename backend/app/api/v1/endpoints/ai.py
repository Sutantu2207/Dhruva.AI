"""REST API endpoints for Domain 11 AI Orchestration, Mentoring, and Copilot workflows."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_db, get_current_user, require_roles
from app.core.security import UserRole
from app.domains.identity.models import User
from app.domains.ai.models import (
    AIConversation,
    AIMessage,
    AIUsageRecord,
    AIAuditEvent,
)
from app.domains.ai.schemas import (
    AIConversationResponse,
    AIMessageResponse,
    CreateConversationPayload,
    SendMessagePayload,
    AIFeedbackPayload,
    AIUsageMetricsResponse,
)
from app.domains.ai.services.conversation_service import AIOrchestrationService
from app.domains.ai.providers.gemini import GeminiProvider

router = APIRouter(prefix="/ai", tags=["AI Orchestration & Mentoring"])


# =========================================================================
# 1. Conversation Lifecycle Endpoints
# =========================================================================

@router.get("/conversations", response_model=List[AIConversationResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List authenticated user's active AI conversations."""
    stmt = (
        select(AIConversation)
        .where(
            AIConversation.user_id == current_user.id,
            AIConversation.status == "active",
        )
        .order_by(AIConversation.last_activity_at.desc())
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.post("/conversations", response_model=AIConversationResponse)
async def create_conversation(
    payload: CreateConversationPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new role-scoped AI conversation."""
    return await AIOrchestrationService.create_conversation(db, current_user, payload)


@router.get("/conversations/{conversation_id}", response_model=AIConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch conversation details and bounded message history with citations."""
    stmt = select(AIConversation).where(AIConversation.id == conversation_id)
    res = await db.execute(stmt)
    conv = res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    if conv.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return conv


@router.post("/conversations/{conversation_id}/messages", response_model=AIMessageResponse)
async def send_message(
    conversation_id: str,
    payload: SendMessagePayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send conversational turn to AI Orchestration Gateway with deterministic grounding."""
    return await AIOrchestrationService.process_user_turn(
        db, conversation_id=conversation_id, user=current_user, payload=payload
    )


@router.post("/messages/{message_id}/feedback")
async def submit_feedback(
    message_id: str,
    payload: AIFeedbackPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit quality evaluation feedback on an AI message."""
    fb = await AIOrchestrationService.record_feedback(db, message_id, current_user, payload)
    return {"status": "success", "feedback_id": fb.id}


# =========================================================================
# 2. Institutional Usage & Governance Observability
# =========================================================================

@router.get("/usage", response_model=AIUsageMetricsResponse)
async def get_usage_metrics(
    current_user: User = Depends(require_roles(UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Institutional observability on token consumption, estimated costs, and safety audits."""
    c_stmt = select(func.count(AIConversation.id))
    m_stmt = select(func.count(AIMessage.id))
    u_stmt = select(
        func.sum(AIUsageRecord.input_tokens),
        func.sum(AIUsageRecord.output_tokens),
        func.sum(AIUsageRecord.estimated_cost),
    )
    a_stmt = select(func.count(AIAuditEvent.id))

    c_cnt = (await db.execute(c_stmt)).scalar() or 0
    m_cnt = (await db.execute(m_stmt)).scalar() or 0
    u_row = (await db.execute(u_stmt)).first()
    in_tok = u_row[0] or 0 if u_row else 0
    out_tok = u_row[1] or 0 if u_row else 0
    est_cost = u_row[2] or 0 if u_row else 0
    a_cnt = (await db.execute(a_stmt)).scalar() or 0

    return AIUsageMetricsResponse(
        total_conversations=c_cnt,
        total_messages=m_cnt,
        total_input_tokens=in_tok,
        total_output_tokens=out_tok,
        estimated_total_cost=est_cost,
        audit_events_count=a_cnt,
    )


@router.get("/trust")
async def get_ai_trust_manifest():
    """Public transparency manifest explaining privacy boundaries and authority limits."""
    provider = GeminiProvider()
    return {
        "platform": "Dhruva.AI Sovereign Academic Operating System",
        "governance_model": "Controlled Grounded AI Companion",
        "authority_boundary": {
            "grades_and_mastery": "Authoritative Deterministic Engines (Domains 5 & 6)",
            "career_readiness": "Deterministic Trajectory Models (Domain 7)",
            "remediation_priority": "Observable Defect Formula (Domain 10)",
            "llm_role": "Natural Language Interface, Tutor, and Grounded Explainer",
        },
        "privacy": {
            "pii_minimization": "Enabled (Emails, phone numbers, and secrets scrubbed prior to inference)",
            "database_access": "Zero direct database queries permitted from LLM",
        },
        "provider_health": provider.health_check(),
    }
