"""Deterministic Audit Logging Service.

Maintains an immutable structured log of security, authorization, and AI interactions.
"""

from datetime import datetime, timezone
import hashlib
import json
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.core.logging import logger
from app.core.security import UserRole


class AuditEvent(BaseModel):
    event_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor_id: str
    actor_role: UserRole
    event_type: str
    resource_type: str
    resource_id: str
    payload_hash: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


def compute_payload_hash(data: Any) -> str:
    """Computes SHA-256 hash of arbitrary payload data."""
    encoded = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def record_audit_event(
    actor_id: str,
    actor_role: UserRole,
    event_type: str,
    resource_type: str,
    resource_id: str,
    payload: Optional[Dict[str, Any]] = None,
) -> AuditEvent:
    """Creates and logs a structured audit event."""
    payload_data = payload or {}
    payload_hash = compute_payload_hash(payload_data)
    event_id = hashlib.sha256(f"{actor_id}:{event_type}:{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()[:16]

    event = AuditEvent(
        event_id=event_id,
        actor_id=actor_id,
        actor_role=actor_role,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        payload_hash=payload_hash,
        metadata={"payload_keys": list(payload_data.keys())},
    )

    logger.info(
        f"AUDIT: [{event.event_type}] actor={event.actor_id} ({event.actor_role.value}) "
        f"target={event.resource_type}:{event.resource_id} hash={event.payload_hash[:8]}"
    )
    return event
