"""Production-grade system health, readiness, and liveness endpoints.

READINESS INVARIANTS:
1. /health/live: Verifies process liveness without touching external dependencies.
2. /health/ready: Probes core database and required state. Non-critical dependencies (e.g. AI provider)
   mark status as 'degraded' rather than crashing the readiness probe.
3. No secrets or credentials are ever leaked in health responses.
"""

from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, status, Response
from pydantic import BaseModel
from app.core.config import settings
from app.core.database import check_database_health
from app.core.redis import redis_manager
from app.core.worker import job_worker
from app.domains.ai.providers.gemini import gemini_provider
from app import __version__

router = APIRouter(tags=["Health & Operations"])


class LivenessResponse(BaseModel):
    status: str
    timestamp: datetime


class ReadinessResponse(BaseModel):
    status: str  # healthy, degraded, unhealthy
    version: str
    environment: str
    timestamp: datetime
    database: Dict[str, Any]
    redis: Dict[str, Any]
    workers: Dict[str, Any]
    ai_provider: Dict[str, Any]


@router.get("/health/live", response_model=LivenessResponse)
async def liveness_probe() -> LivenessResponse:
    """Kubernetes/Container liveness probe to verify process is alive."""
    return LivenessResponse(
        status="alive",
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness_probe(response: Response) -> ReadinessResponse:
    """Production readiness probe evaluating required platform dependencies."""
    # 1. Database check
    db_health = await check_database_health()
    db_ok = db_health.get("connected", False)

    # 2. Redis check
    redis_health = await redis_manager.health_check()

    # 3. Worker check
    worker_metrics = job_worker.get_metrics()

    # 4. AI check (non-blocking: lack of key in dev/staging is degraded, not fatal)
    ai_health = gemini_provider.health_check()

    # Determine overall readiness
    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        overall_status = "unhealthy"
    elif redis_health.get("status") == "degraded" or ai_health.get("status") != "healthy":
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    return ReadinessResponse(
        status=overall_status,
        version=__version__,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc),
        database=db_health,
        redis=redis_health,
        workers=worker_metrics,
        ai_provider=ai_health,
    )


@router.get("/health", response_model=ReadinessResponse)
async def general_health(response: Response) -> ReadinessResponse:
    """Convenience alias for /health/ready."""
    return await readiness_probe(response)
