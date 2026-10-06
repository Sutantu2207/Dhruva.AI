"""Domain 12 — Notifications and System Operations Models."""

from datetime import datetime, timezone
import uuid
from typing import Optional
from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Enum as SAEnum,
    Integer,
    JSON,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class NotificationTypeEnum(str):
    INFO = "INFO"
    REMINDER = "REMINDER"
    DEADLINE = "DEADLINE"
    LEARNING = "LEARNING"
    ASSESSMENT = "ASSESSMENT"
    REMEDIATION = "REMEDIATION"
    INTERVENTION = "INTERVENTION"
    MENTOR = "MENTOR"
    PLACEMENT = "PLACEMENT"
    SYSTEM = "SYSTEM"
    SECURITY = "SECURITY"


class Notification(Base):
    """Canonical notification records for users across all academic roles."""

    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    notification_type: Mapped[str] = mapped_column(
        String(32), default=NotificationTypeEnum.INFO, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    link_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        Index("ix_notifications_user_unread", "user_id", "is_read"),
    )


class NotificationPreference(Base):
    """User delivery preferences for notifications."""

    __tablename__ = "notification_preferences"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    learning_reminders: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    assessment_alerts: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    remediation_updates: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    placement_alerts: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
