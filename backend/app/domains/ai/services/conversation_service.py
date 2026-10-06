"""Core Orchestration Service for Domain 11 AI."""

import hashlib
import json
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status

from app.domains.identity.models import User
from app.domains.ai.models import (
    AIConversation,
    AIMessage,
    AIToolInvocation,
    AIRetrievalCitation,
    AIUsageRecord,
    AIAuditEvent,
    AIFeedback,
)
from app.domains.ai.config import (
    AUTHORITY_SYSTEM_INSTRUCTION,
    ESTIMATED_COST_PER_1M_INPUT_TOKENS,
    ESTIMATED_COST_PER_1M_OUTPUT_TOKENS,
)
from app.domains.ai.providers.gemini import GeminiProvider
from app.domains.ai.safety.prompt_injection import PromptInjectionDefense
from app.domains.ai.safety.pii import PIIScrubber
from app.domains.ai.orchestration.context import AIContextResolver
from app.domains.ai.orchestration.tools import AIToolRegistry
from app.domains.ai.retrieval.retriever import ScopedKnowledgeRetriever
from app.domains.ai.schemas import SendMessagePayload, CreateConversationPayload, AIFeedbackPayload


class AIOrchestrationService:
    """End-to-end controlled orchestration service interfacing between users, deterministic engines, and Gemini."""

    @staticmethod
    def _calculate_estimated_cost(input_tokens: int, output_tokens: int) -> Decimal:
        """Calculate estimated cost in USD based on token counts."""
        cost_in = (Decimal(str(input_tokens)) / Decimal("1000000")) * ESTIMATED_COST_PER_1M_INPUT_TOKENS
        cost_out = (Decimal(str(output_tokens)) / Decimal("1000000")) * ESTIMATED_COST_PER_1M_OUTPUT_TOKENS
        return (cost_in + cost_out).quantize(Decimal("0.000001"))

    @staticmethod
    async def create_conversation(
        db: AsyncSession,
        user: User,
        payload: CreateConversationPayload,
    ) -> AIConversation:
        """Initialize a new persistent conversation scoped to user's institutional role."""
        scope = user.role.value.upper() if hasattr(user.role, "value") else str(user.role).upper()
        conv = AIConversation(
            user_id=user.id,
            institution_id=user.institution_id,
            scope=scope,
            title=payload.title or "New Conversation",
            current_mode=payload.current_mode,
        )
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        return conv

    @staticmethod
    async def process_user_turn(
        db: AsyncSession,
        conversation_id: str,
        user: User,
        payload: SendMessagePayload,
        provider: Optional[GeminiProvider] = None,
    ) -> AIMessage:
        """Process conversational turn with injection defense, context resolution, tool execution, and grounding."""
        # 1. Fetch Conversation & Check Authorization
        c_res = await db.execute(select(AIConversation).where(AIConversation.id == conversation_id))
        conv = c_res.scalar_one_or_none()
        if not conv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        if conv.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this conversation")

        # 2. Prompt Injection Defense
        is_injection, matched_patterns = PromptInjectionDefense.scan_for_injection(payload.content)
        if is_injection:
            # Audit Security Event
            audit = AIAuditEvent(
                user_id=user.id,
                institution_id=user.institution_id,
                event_type="PROMPT_INJECTION_BLOCKED",
                scope=conv.scope,
                event_metadata={"matched_patterns": matched_patterns, "input_snippet": payload.content[:100]},
            )
            db.add(audit)
            await db.commit()

            # Record refusal message
            refusal_msg = AIMessage(
                conversation_id=conv.id,
                role="ASSISTANT",
                content=(
                    "I cannot process this request because it violates Dhruva.AI safety policies. "
                    "All platform decisions remain deterministic, verified, and protected by strict authorization."
                ),
                status="filtered",
            )
            db.add(refusal_msg)
            await db.commit()
            await db.refresh(refusal_msg)
            return refusal_msg

        # 3. Record User Message
        user_msg = AIMessage(
            conversation_id=conv.id,
            role="USER",
            content=payload.content,
        )
        db.add(user_msg)
        await db.flush()

        # 4. Context & Role Scope Resolution
        user_context = await AIContextResolver.resolve_user_context(db, user)

        # 5. Deterministic Tool Execution & RAG Grounding
        tool_results: List[Dict[str, Any]] = []
        citations_data: List[Dict[str, Any]] = []

        # If student query mentions mastery or weaknesses, invoke get_student_mastery
        content_lower = payload.content.lower()
        if "mastery" in content_lower or "weak" in content_lower or "struggling" in content_lower:
            tool_res = await AIToolRegistry.execute_tool(
                db, user, user_context, "get_student_mastery", {"concept_id": payload.context_concept_id}
            )
            tool_results.append({"tool": "get_student_mastery", "result": tool_res})

        # If student query mentions remediation, invoke get_student_remediation
        if "remediation" in content_lower or "recovery" in content_lower:
            rem_res = await AIToolRegistry.execute_tool(
                db, user, user_context, "get_student_remediation", {}
            )
            tool_results.append({"tool": "get_student_remediation", "result": rem_res})

        # RAG Retrieval
        retrieved_content = await ScopedKnowledgeRetriever.retrieve_approved_content(
            db, query=payload.content, institution_id=user.institution_id, concept_id=payload.context_concept_id
        )
        citations_data.extend(retrieved_content)

        # 6. Assemble Grounded Messages for Gemini
        system_grounding = f"{AUTHORITY_SYSTEM_INSTRUCTION}\n\nUSER CONTEXT:\n{json.dumps(PIIScrubber.sanitize_context_payload(user_context))}"
        if tool_results:
            system_grounding += f"\n\nVERIFIED DETERMINISTIC ENGINE DATA:\n{json.dumps(tool_results)}"
        if citations_data:
            system_grounding += f"\n\nRETRIEVED APPROVED CURRICULUM SOURCES:\n{json.dumps([c['title'] + ': ' + c.get('content_snippet', '') for c in citations_data])}"

        # Fetch recent bounded conversation messages (last 6 turns)
        history_stmt = (
            select(AIMessage)
            .where(AIMessage.conversation_id == conv.id)
            .order_by(AIMessage.created_at.desc())
            .limit(6)
        )
        h_res = await db.execute(history_stmt)
        recent_history = list(reversed(h_res.scalars().all()))

        prompt_messages = [
            {"role": m.role.lower(), "content": m.content}
            for m in recent_history
        ]

        # 7. Call Gemini Provider
        ai_provider = provider or GeminiProvider()
        ai_resp = await ai_provider.generate(
            messages=prompt_messages,
            system_instruction=system_grounding,
            temperature=0.2,
        )

        # 8. Store Assistant Message, Tools, Citations & Token Usage
        asst_msg = AIMessage(
            conversation_id=conv.id,
            role="ASSISTANT",
            content=ai_resp.content,
            provider=ai_resp.model,
            model=ai_resp.model,
            input_tokens=ai_resp.input_tokens,
            output_tokens=ai_resp.output_tokens,
            latency_ms=ai_resp.latency_ms,
            status="completed",
        )
        db.add(asst_msg)
        await db.flush()

        # Log Tools
        for t in tool_results:
            t_inv = AIToolInvocation(
                conversation_id=conv.id,
                message_id=asst_msg.id,
                tool_name=t["tool"],
                arguments_hash=hashlib.sha256(json.dumps(t).encode()).hexdigest()[:16],
                result_summary=t["result"],
                status="success",
                latency_ms=10,
            )
            db.add(t_inv)

        # Log Citations
        for c in citations_data:
            cit = AIRetrievalCitation(
                message_id=asst_msg.id,
                source_type=c["source_type"],
                source_id=c["source_id"],
                title=c["title"],
                chunk_id=c.get("chunk_id"),
                relevance_score=c.get("relevance_score", 1.0),
            )
            db.add(cit)

        # Record Cost & Usage
        est_cost = AIOrchestrationService._calculate_estimated_cost(
            ai_resp.input_tokens, ai_resp.output_tokens
        )
        usage = AIUsageRecord(
            user_id=user.id,
            institution_id=user.institution_id,
            provider="gemini",
            model=ai_resp.model,
            input_tokens=ai_resp.input_tokens,
            output_tokens=ai_resp.output_tokens,
            estimated_cost=est_cost,
        )
        db.add(usage)

        conv.last_activity_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(asst_msg)
        return asst_msg

    @staticmethod
    async def record_feedback(
        db: AsyncSession,
        message_id: str,
        user: User,
        payload: AIFeedbackPayload,
    ) -> AIFeedback:
        """Capture student or instructor feedback for continuous evaluation."""
        m_res = await db.execute(select(AIMessage).where(AIMessage.id == message_id))
        msg = m_res.scalar_one_or_none()
        if not msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI message not found")

        feedback = AIFeedback(
            message_id=message_id,
            user_id=user.id,
            rating=payload.rating,
            reason=payload.reason,
            comment=payload.comment,
        )
        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)
        return feedback
