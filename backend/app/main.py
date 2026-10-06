from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import logger
from app.core.redis import redis_manager
from app.core.worker import job_worker
from app.core.scheduler import scheduler
from app.api.v1.router import api_router
from app import __version__


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle management."""
    # 1. Startup validation
    settings.validate_production_secrets()
    logger.info(
        f"Starting {settings.PROJECT_NAME} v{__version__} "
        f"[env={settings.ENVIRONMENT}] [debug={settings.DEBUG}]"
    )

    # 2. Initialize distributed caching / coordination
    await redis_manager.initialize()

    # 3. Start background job worker and scheduler
    job_worker.start()
    scheduler.start()

    yield

    # 4. Graceful shutdown
    logger.info(f"Shutting down {settings.PROJECT_NAME}")
    await scheduler.stop()
    await job_worker.stop()
    await redis_manager.close()


def create_application() -> FastAPI:
    """Application factory configuring middleware and routes."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=__version__,
        description="Production-grade backend for Dhruva.AI education and career intelligence platform",
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Production Security Headers Middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "object-src 'none'; "
            "base-uri 'self';"
        )
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    # Mount root-level health probes for container & platform ingress (Railway, Kubernetes, Docker)
    from app.api.v1.endpoints.health import router as health_router
    app.include_router(health_router)

    # Root API metadata endpoint
    @app.get("/", tags=["Health & Operations"])
    async def root_status():
        """Root API metadata and operational status."""
        return {
            "name": settings.PROJECT_NAME,
            "version": __version__,
            "environment": settings.ENVIRONMENT,
            "status": "healthy",
            "health_live": "/health/live",
            "health_ready": "/health/ready",
            "api_prefix": settings.API_V1_PREFIX,
        }

    # Mount API v1 router
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_application()
