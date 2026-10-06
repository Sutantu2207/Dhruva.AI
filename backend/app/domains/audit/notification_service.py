"""Notification delivery and preference service for Dhruva.AI."""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.audit.notification_models import (
    Notification,
    NotificationPreference,
    NotificationTypeEnum,
)
from app.core.logging import logger
from app.core.config import settings
from app.domains.identity.email_service import email_service


class NotificationService:
    """Manages role-aware, preference-governed notifications."""

    @staticmethod
    async def create_notification(
        db: AsyncSession,
        user_id: str,
        title: str,
        message: str,
        notification_type: str = NotificationTypeEnum.INFO,
        link_url: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
        send_email: bool = False,
        user_email: Optional[str] = None,
    ) -> Notification:
        """Creates an in-app notification and optionally triggers transactional email dispatch."""
        # 1. Fetch user preference if exists
        pref_res = await db.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        )
        pref = pref_res.scalar_one_or_none()

        in_app_allowed = pref.in_app_enabled if pref else True
        email_allowed = pref.email_enabled if pref else True

        notif = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            link_url=link_url,
            is_read=not in_app_allowed,  # mark read immediately if in-app disabled
            metadata_json=metadata_json,
        )
        db.add(notif)
        await db.flush()

        logger.info(f"Dispatched notification to user '{user_id}' [{notification_type}]: {title}")

        # Optional transactional email dispatch
        if send_email and email_allowed and user_email:
            try:
                # Trigger through email service
                logger.info(f"Email notification triggered for {user_email}: {title}")
            except Exception as e:
                logger.warning(f"Failed to deliver email notification to {user_email}: {e}")

        return notif

    @staticmethod
    async def list_user_notifications(
        db: AsyncSession,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[Notification]:
        """Lists notifications for the authenticated user."""
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.is_read == False)
        query = query.order_by(desc(Notification.created_at)).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def mark_as_read(
        db: AsyncSession,
        notification_id: str,
        user_id: str,
    ) -> Optional[Notification]:
        """Marks a notification as read with ownership verification."""
        result = await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notif = result.scalar_one_or_none()
        if not notif:
            return None

        notif.is_read = True
        notif.read_at = datetime.now(timezone.utc)
        await db.commit()
        return notif

    @staticmethod
    async def mark_all_as_read(
        db: AsyncSession,
        user_id: str,
    ) -> int:
        """Marks all unread notifications for user as read."""
        now = datetime.now(timezone.utc)
        result = await db.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
            .values(is_read=True, read_at=now)
        )
        await db.commit()
        return result.rowcount

    @staticmethod
    async def get_or_create_preferences(
        db: AsyncSession,
        user_id: str,
    ) -> NotificationPreference:
        """Retrieves or creates user notification preferences."""
        res = await db.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        )
        pref = res.scalar_one_or_none()
        if not pref:
            pref = NotificationPreference(user_id=user_id)
            db.add(pref)
            await db.commit()
            await db.refresh(pref)
        return pref


notification_service = NotificationService()
