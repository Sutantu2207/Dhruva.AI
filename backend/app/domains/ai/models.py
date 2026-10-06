"""SQLAlchemy Models for Domain 11: System-wide AI Orchestration & Natural Language Layer."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    String,
    Text,
    Integer,
    Numeric,
    DateTime,
    ForeignKey,
    JSON,
    Boolean,
    Float,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


# =========================================================================
# 1. AI Conversation
# =========================================================================

class AIConversation(Base):
    """Scoped persistent conversation container with bounded context."""
    __tablename__ = "ai_conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    institution_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=True
    )
    scope: Mapped[str] = mapped_column(
        String(32), index=True, nullable=False
    )  # STUDENT, FACULTY, MENTOR, HOD, PLACEMENT, ADMIN
    title: Mapped[str] = mapped_column(String(255), default="New Conversation", nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="active", index=True, nullable=False
    )  # active, archived, deleted
    current_mode: Mapped[str] = mapped_column(
        String(32), default="EXPLAIN", nullable=False
    )  # EXPLAIN, SOCRATIC, PRACTICE, REVIEW, EXAM_PREP, PROJECT_GUIDANCE

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User")  # noqa: F821
    institution: Mapped[Optional["Institution"]] = relationship("Institution")  # noqa: F821

    messages: Mapped[List["AIMessage"]] = relationship(
        "AIMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="AIMessage.created_at", lazy="selectin"
    )


# =========================================================================
# 2. AI Message
# =========================================================================

class AIMessage(Base):
    """Individual conversational exchange turn."""
    __tablename__ = "ai_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ai_conversations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)  # USER, ASSISTANT, SYSTEM, TOOL
    content: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(String(64), default="gemini", nullable=False)
    model: Mapped[str] = mapped_column(String(64), default="gemini-1.5-pro", nullable=False)

    input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="completed", nullable=False)  # completed, failed, filtered

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    conversation: Mapped["AIConversation"] = relationship("AIConversation", back_populates="messages")
    tool_invocations: Mapped[List["AIToolInvocation"]] = relationship(
        "AIToolInvocation", back_populates="message", cascade="all, delete-orphan", lazy="selectin"
    )
    citations: Mapped[List["AIRetrievalCitation"]] = relationship(
        "AIRetrievalCitation", back_populates="message", cascade="all, delete-orphan", lazy="selectin"
    )
    feedback: Mapped[Optional["AIFeedback"]] = relationship(
        "AIFeedback", back_populates="message", cascade="all, delete-orphan", uselist=False, lazy="selectin"
    )


# =========================================================================
# 3. AI Tool Invocation
# =========================================================================

class AIToolInvocation(Base):
    """Audit log of an authorized deterministic tool called by AI."""
    __tablename__ = "ai_tool_invocations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ai_conversations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    message_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ai_messages.id", ondelete="CASCADE"), index=True, nullable=False
    )
    tool_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    arguments_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    result_summary: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="success", nullable=False)  # success, denied, failed
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    message: Mapped["AIMessage"] = relationship("AIMessage", back_populates="tool_invocations")


# =========================================================================
# 4. AI Retrieval Citation
# =========================================================================

class AIRetrievalCitation(Base):
    """Traceable, verifiable citation grounding an AI assertion to an approved source."""
    __tablename__ = "ai_retrieval_citations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ai_messages.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)  # lesson, concept, resource, curriculum
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    chunk_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    relevance_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    message: Mapped["AIMessage"] = relationship("AIMessage", back_populates="citations")


# =========================================================================
# 5. AI Usage Record (Cost & Token Accounting)
# =========================================================================

class AIUsageRecord(Base):
    """Institutional & user token billing, consumption, and audit record."""
    __tablename__ = "ai_usage_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    institution_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=True
    )
    provider: Mapped[str] = mapped_column(String(64), default="gemini", nullable=False)
    model: Mapped[str] = mapped_column(String(64), default="gemini-1.5-pro", nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(8, 6), default=Decimal("0.000000"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User")  # noqa: F821
    institution: Mapped[Optional["Institution"]] = relationship("Institution")  # noqa: F821


# =========================================================================
# 6. AI Audit Event
# =========================================================================

class AIAuditEvent(Base):
    """Security audit log for sensitive events, prompt injections, and denials."""
    __tablename__ = "ai_audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    institution_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=True
    )
    event_type: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False
    )  # PROMPT_INJECTION_BLOCKED, PII_REDACTED, TOOL_ACCESS_DENIED, RATE_LIMIT_EXCEEDED, CONTENT_FILTERED
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    tool_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    event_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User")  # noqa: F821
    institution: Mapped[Optional["Institution"]] = relationship("Institution")  # noqa: F821


# =========================================================================
# 7. AI Feedback
# =========================================================================

class AIFeedback(Base):
    """Explicit learner or instructor rating on AI response quality."""
    __tablename__ = "ai_feedbacks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ai_messages.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    rating: Mapped[str] = mapped_column(String(16), nullable=False)  # thumbs_up, thumbs_down
    reason: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # incorrect, unclear, irrelevant, missing_context
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    message: Mapped["AIMessage"] = relationship("AIMessage", back_populates="feedback")
    user: Mapped["User"] = relationship("User")  # noqa: F821


# =========================================================================
# 8. AI Knowledge Document Chunk (RAG Index)
# =========================================================================

class AIKnowledgeChunk(Base):
    """Pre-chunked approved curriculum content for scoped vector retrieval."""
    __tablename__ = "ai_knowledge_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=True
    )
    source_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # lesson, concept, curriculum
    source_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    version_id: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    access_scope: Mapped[str] = mapped_column(String(32), default="public", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
