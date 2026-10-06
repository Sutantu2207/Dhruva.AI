"""Notification REST Endpoints for Dhruva.AI."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.api.deps import get_current_user
from app.domains.identity.models import User
from app.domains.audit.notification_service import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    notification_type: str
    title: str
    message: str
    link_url: Optional[str]
    is_read: bool
    created_at: str


class NotificationPreferencesUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    learning_reminders: Optional[bool] = None
    assessment_alerts: Optional[bool] = None
    remediation_updates: Optional[bool] = None
    placement_alerts: Optional[bool] = None


@router.get("", response_model=List[NotificationResponse])
async def list_notifications(
    unread_only: bool = False,
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> List[NotificationResponse]:
    """Retrieves notifications for the current authenticated user."""
    items = await notification_service.list_user_notifications(
        db, user_id=current_user.id, unread_only=unread_only, limit=limit
    )
    return [
        NotificationResponse(
            id=item.id,
            notification_type=item.notification_type,
            title=item.title,
            message=item.message,
            link_url=item.link_url,
            is_read=item.is_read,
            created_at=item.created_at.isoformat(),
        )
        for item in items
    ]


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> NotificationResponse:
    """Marks a single notification as read."""
    item = await notification_service.mark_as_read(db, notification_id, current_user.id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return NotificationResponse(
        id=item.id,
        notification_type=item.notification_type,
        title=item.title,
        message=item.message,
        link_url=item.link_url,
        is_read=item.is_read,
        created_at=item.created_at.isoformat(),
    )


@router.post("/read-all")
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Marks all user notifications as read."""
    count = await notification_service.mark_all_as_read(db, current_user.id)
    return {"status": "success", "marked_read_count": count}


@router.get("/preferences")
async def get_notification_preferences(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Retrieves notification delivery preferences."""
    pref = await notification_service.get_or_create_preferences(db, current_user.id)
    return {
        "email_enabled": pref.email_enabled,
        "in_app_enabled": pref.in_app_enabled,
        "learning_reminders": pref.learning_reminders,
        "assessment_alerts": pref.assessment_alerts,
        "remediation_updates": pref.remediation_updates,
        "placement_alerts": pref.placement_alerts,
    }


@router.put("/preferences")
async def update_notification_preferences(
    payload: NotificationPreferencesUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Updates user notification delivery preferences."""
    pref = await notification_service.get_or_create_preferences(db, current_user.id)
    if payload.email_enabled is not None:
        pref.email_enabled = payload.email_enabled
    if payload.in_app_enabled is not None:
        pref.in_app_enabled = payload.in_app_enabled
    if payload.learning_reminders is not None:
        pref.learning_reminders = payload.learning_reminders
    if payload.assessment_alerts is not None:
        pref.assessment_alerts = payload.assessment_alerts
    if payload.remediation_updates is not None:
        pref.remediation_updates = payload.remediation_updates
    if payload.placement_alerts is not None:
        pref.placement_alerts = payload.placement_alerts

    await db.commit()
    return {"status": "success", "message": "Notification preferences updated"}
