"""Audit logging helper for Domain 3 events."""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.identity.models import Base
from sqlalchemy import String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class DomainAuditLog(Base):
    """General audit log for domain mutations (profile changes, verifications, status updates)."""
    __tablename__ = "domain_audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)
    actor_user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


async def record_audit_log(
    db: AsyncSession,
    actor_user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    institution_id: Optional[str] = None,
    metadata_payload: Optional[Dict[str, Any]] = None,
) -> DomainAuditLog:
    """Helper to record an immutable audit log entry."""
    entry = DomainAuditLog(
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        institution_id=institution_id,
        metadata_payload=metadata_payload or {},
    )
    db.add(entry)
    return entry
