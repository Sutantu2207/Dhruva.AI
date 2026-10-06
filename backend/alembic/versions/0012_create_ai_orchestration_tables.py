"""Alembic migration 0012: Create AI Orchestration tables.

Revision ID: 0012_create_ai_orchestration
Revises: 0011_create_adaptive_remediation
Create Date: 2026-10-06 13:17:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0012_create_ai_orchestration"
down_revision: Union[str, None] = "0011_create_adaptive_remediation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. ai_conversations
    op.create_table(
        "ai_conversations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), server_default="New Conversation", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("current_mode", sa.String(length=32), server_default="EXPLAIN", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_conversations_user_id", "ai_conversations", ["user_id"])
    op.create_index("ix_ai_conversations_institution_id", "ai_conversations", ["institution_id"])
    op.create_index("ix_ai_conversations_scope", "ai_conversations", ["scope"])
    op.create_index("ix_ai_conversations_status", "ai_conversations", ["status"])

    # 2. ai_messages
    op.create_table(
        "ai_messages",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("conversation_id", sa.String(length=36), sa.ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=64), server_default="gemini", nullable=False),
        sa.Column("model", sa.String(length=64), server_default="gemini-1.5-pro", nullable=False),
        sa.Column("input_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("output_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("latency_ms", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="completed", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_messages_conversation_id", "ai_messages", ["conversation_id"])

    # 3. ai_tool_invocations
    op.create_table(
        "ai_tool_invocations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("conversation_id", sa.String(length=36), sa.ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("message_id", sa.String(length=36), sa.ForeignKey("ai_messages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tool_name", sa.String(length=128), nullable=False),
        sa.Column("arguments_hash", sa.String(length=64), nullable=False),
        sa.Column("result_summary", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="success", nullable=False),
        sa.Column("latency_ms", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_tool_invocations_conversation_id", "ai_tool_invocations", ["conversation_id"])
    op.create_index("ix_ai_tool_invocations_message_id", "ai_tool_invocations", ["message_id"])
    op.create_index("ix_ai_tool_invocations_tool_name", "ai_tool_invocations", ["tool_name"])

    # 4. ai_retrieval_citations
    op.create_table(
        "ai_retrieval_citations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("message_id", sa.String(length=36), sa.ForeignKey("ai_messages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("chunk_id", sa.String(length=64), nullable=True),
        sa.Column("relevance_score", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_retrieval_citations_message_id", "ai_retrieval_citations", ["message_id"])

    # 5. ai_usage_records
    op.create_table(
        "ai_usage_records",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("provider", sa.String(length=64), server_default="gemini", nullable=False),
        sa.Column("model", sa.String(length=64), server_default="gemini-1.5-pro", nullable=False),
        sa.Column("input_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("output_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("estimated_cost", sa.Numeric(precision=8, scale=6), server_default="0.000000", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_usage_records_user_id", "ai_usage_records", ["user_id"])
    op.create_index("ix_ai_usage_records_institution_id", "ai_usage_records", ["institution_id"])

    # 6. ai_audit_events
    op.create_table(
        "ai_audit_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("tool_name", sa.String(length=128), nullable=True),
        sa.Column("event_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_audit_events_user_id", "ai_audit_events", ["user_id"])
    op.create_index("ix_ai_audit_events_institution_id", "ai_audit_events", ["institution_id"])
    op.create_index("ix_ai_audit_events_event_type", "ai_audit_events", ["event_type"])

    # 7. ai_feedbacks
    op.create_table(
        "ai_feedbacks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("message_id", sa.String(length=36), sa.ForeignKey("ai_messages.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.String(length=16), nullable=False),
        sa.Column("reason", sa.String(length=64), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_feedbacks_message_id", "ai_feedbacks", ["message_id"], unique=True)
    op.create_index("ix_ai_feedbacks_user_id", "ai_feedbacks", ["user_id"])

    # 8. ai_knowledge_chunks
    op.create_table(
        "ai_knowledge_chunks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.String(length=36), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("version_id", sa.Integer(), server_default="1", nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("chunk_index", sa.Integer(), server_default="0", nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("metadata_payload", sa.JSON(), nullable=False),
        sa.Column("access_scope", sa.String(length=32), server_default="public", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_knowledge_chunks_institution_id", "ai_knowledge_chunks", ["institution_id"])
    op.create_index("ix_ai_knowledge_chunks_source_type", "ai_knowledge_chunks", ["source_type"])
    op.create_index("ix_ai_knowledge_chunks_source_id", "ai_knowledge_chunks", ["source_id"])


def downgrade() -> None:
    op.drop_table("ai_knowledge_chunks")
    op.drop_table("ai_feedbacks")
    op.drop_table("ai_audit_events")
    op.drop_table("ai_usage_records")
    op.drop_table("ai_retrieval_citations")
    op.drop_table("ai_tool_invocations")
    op.drop_table("ai_messages")
    op.drop_table("ai_conversations")
