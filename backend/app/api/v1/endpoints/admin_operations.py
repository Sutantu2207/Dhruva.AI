"""Administrative Operations and Observability Endpoints.

ROLE SCOPING:
Restricted strictly to 'institution_admin' and 'super_admin' roles.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.api.deps import require_roles
from app.core.worker import job_worker
from app.core.scheduler import scheduler
from app.core.redis import redis_manager
from app.core.config import settings
from app.domains.ai.providers.gemini import gemini_provider
from app.domains.ai.services.conversation_service import AIOrchestrationService
from app.domains.identity.models import User

from app.core.security import UserRole

router = APIRouter(prefix="/admin/operations", tags=["Admin Operations"])


class AdminOperationsOverview(BaseModel):
    environment: str
    feature_flags: Dict[str, bool]
    worker_metrics: Dict[str, Any]
    scheduler_status: Dict[str, Any]
    redis_status: Dict[str, Any]
    ai_status: Dict[str, Any]


@router.get("/overview", response_model=AdminOperationsOverview)
async def get_operations_overview(
    current_user: User = Depends(require_roles(UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
) -> AdminOperationsOverview:
    """Provides a consolidated operational overview of platform sub-systems."""
    redis_health = await redis_manager.health_check()
    ai_health = gemini_provider.health_check()

    return AdminOperationsOverview(
        environment=settings.ENVIRONMENT,
        feature_flags={
            "AI_ENABLED": settings.FEATURE_AI_ENABLED,
            "NOTIFICATIONS_ENABLED": settings.FEATURE_NOTIFICATIONS_ENABLED,
            "BACKGROUND_WORKERS_ENABLED": settings.FEATURE_BACKGROUND_WORKERS_ENABLED,
            "PUBLIC_PORTFOLIOS_ENABLED": settings.FEATURE_PUBLIC_PORTFOLIOS_ENABLED,
            "PLACEMENT_MODULE_ENABLED": settings.FEATURE_PLACEMENT_MODULE_ENABLED,
            "ADVANCED_ANALYTICS_ENABLED": settings.FEATURE_ADVANCED_ANALYTICS_ENABLED,
        },
        worker_metrics=job_worker.get_metrics(),
        scheduler_status=scheduler.get_status(),
        redis_status=redis_health,
        ai_status=ai_health,
    )


@router.get("/jobs")
async def get_worker_jobs(
    limit: int = 20,
    current_user: User = Depends(require_roles(UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
) -> List[Dict[str, Any]]:
    """Lists recent background job execution summaries."""
    return job_worker.get_recent_jobs(limit=limit)


@router.get("/ai")
async def get_ai_operations(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
) -> Dict[str, Any]:
    """Retrieves institutional AI token usage and operational costs."""
    metrics = await AIOrchestrationService.get_usage_metrics(
        db,
        institution_id=current_user.institution_id if current_user.role != "super_admin" else None,
    )
    return metrics.model_dump() if hasattr(metrics, "model_dump") else dict(metrics)


@router.get("/storage")
async def get_storage_operations(
    current_user: User = Depends(require_roles(UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
) -> Dict[str, Any]:
    """Returns object storage configuration and backend status."""
    return {
        "backend": settings.STORAGE_BACKEND,
        "bucket": settings.S3_BUCKET_NAME if settings.STORAGE_BACKEND == "s3" else "local",
        "local_dir": settings.STORAGE_LOCAL_DIR if settings.STORAGE_BACKEND == "local" else None,
        "region": settings.S3_REGION,
        "status": "ready",
    }
