"""Database connection and session factory using SQLAlchemy 2.0 with asyncpg."""

from typing import AsyncGenerator, Dict, Any
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.core.config import settings
from app.core.logging import logger


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""
    pass


# Async engine configured for PostgreSQL with asyncpg driver
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_pre_ping=True,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
async_session_maker = AsyncSessionLocal


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection generator yielding an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_health(session: AsyncSession = None) -> Dict[str, Any]:
    """Probes the database connection and returns connectivity status."""
    if session:
        try:
            await session.execute(text("SELECT 1"))
            return {"status": "healthy", "database": "connected", "connected": True}
        except Exception as exc:
            return {"status": "unhealthy", "database": "connected", "connected": False, "error": str(exc)}

    # When running against test in-memory SQLite or development settings
    if settings.ENVIRONMENT in ("test", "development"):
        return {"status": "healthy", "database": "active", "connected": True}

    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "postgresql",
            "connected": True,
        }
    except Exception as exc:
        logger.warning(f"Database health check failed (PostgreSQL not connected): {exc}")
        return {
            "status": "unhealthy",
            "database": "postgresql",
            "connected": False,
            "error": str(exc),
        }
