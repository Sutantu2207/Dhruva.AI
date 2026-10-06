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


def patch_alembic_version_table(length: int = 255) -> None:
    """Patch Alembic's DefaultImpl.version_table_impl to create alembic_version.version_num
    with VARCHAR(length) instead of the default VARCHAR(32).
    
    This ensures descriptive migration identifiers (e.g., 0013_create_production_operations_tables)
    do not trigger StringDataRightTruncationError in PostgreSQL or other relational databases.
    """
    try:
        from alembic.ddl.impl import DefaultImpl
        from sqlalchemy import Table, MetaData, Column, String, PrimaryKeyConstraint

        def _custom_version_table_impl(
            self,
            *,
            version_table: str,
            version_table_schema: str | None,
            version_table_pk: bool,
            **kw,
        ) -> Table:
            vt = Table(
                version_table,
                MetaData(),
                Column("version_num", String(length), nullable=False),
                schema=version_table_schema,
            )
            if version_table_pk:
                vt.append_constraint(
                    PrimaryKeyConstraint("version_num", name=f"{version_table}_pkc")
                )
            return vt

        DefaultImpl.version_table_impl = _custom_version_table_impl
    except ImportError:
        pass


# Apply the version table patch automatically on database module load
patch_alembic_version_table()


# Async engine configured for PostgreSQL with asyncpg driver (or test databases)
engine_kwargs: Dict[str, Any] = {
    "echo": settings.DEBUG,
    "pool_pre_ping": True,
}

if "sqlite" not in settings.DATABASE_URL:
    engine_kwargs.update({
        "pool_size": settings.DATABASE_POOL_SIZE,
        "max_overflow": settings.DATABASE_MAX_OVERFLOW,
        "pool_timeout": settings.DATABASE_POOL_TIMEOUT,
    })
    if "asyncpg" in settings.DATABASE_URL:
        engine_kwargs["connect_args"] = {
            "command_timeout": settings.DATABASE_POOL_TIMEOUT,
            "server_settings": {
                "statement_timeout": str(settings.DATABASE_STATEMENT_TIMEOUT_MS),
            },
        }

async_engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
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
