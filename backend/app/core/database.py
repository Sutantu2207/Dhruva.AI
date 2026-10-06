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

            # Safe diagnostic introspection without leaking credentials
            current_db = (await conn.execute(text("SELECT current_database()"))).scalar()
            current_schema = (await conn.execute(text("SELECT current_schema()"))).scalar()
            search_path = (await conn.execute(text("SHOW search_path"))).scalar()

            has_inst_public = (await conn.execute(text("SELECT to_regclass('public.institutions')"))).scalar() is not None
            has_sess_public = (await conn.execute(text("SELECT to_regclass('public.user_sessions')"))).scalar() is not None
            has_inst_any = (await conn.execute(text("SELECT to_regclass('institutions')"))).scalar() is not None
            has_sess_any = (await conn.execute(text("SELECT to_regclass('user_sessions')"))).scalar() is not None

            has_alembic_table = (await conn.execute(text("SELECT to_regclass('public.alembic_version')"))).scalar() is not None
            alembic_rev = None
            if has_alembic_table:
                try:
                    alembic_res = await conn.execute(text("SELECT version_num FROM alembic_version"))
                    alembic_rev = alembic_res.scalar()
                except Exception:
                    await conn.rollback()

            # Inspect all databases on this PostgreSQL cluster
            db_list_res = await conn.execute(text("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname"))
            available_dbs = [r[0] for r in db_list_res.fetchall()]

            # Inspect all schemas in current database
            schema_list_res = await conn.execute(text("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name"))
            available_schemas = [r[0] for r in schema_list_res.fetchall()]

            # Inspect all tables in current database public schema
            tables_res = await conn.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
            ))
            all_tables = [r[0] for r in tables_res.fetchall()]

            # Also inspect database 'postgres' on the same cluster if current_db != 'postgres'
            postgres_db_info = {}
            if "postgres" in available_dbs and current_db != "postgres":
                try:
                    alt_url = async_engine.url.set(database="postgres")
                    alt_engine = create_async_engine(alt_url)
                    async with alt_engine.connect() as alt_conn:
                        alt_inst = (await alt_conn.execute(text("SELECT to_regclass('public.institutions')"))).scalar() is not None
                        alt_sess = (await alt_conn.execute(text("SELECT to_regclass('public.user_sessions')"))).scalar() is not None
                        alt_alembic_table = (await alt_conn.execute(text("SELECT to_regclass('public.alembic_version')"))).scalar() is not None
                        alt_alembic_rev = None
                        if alt_alembic_table:
                            alt_alembic_rev = (await alt_conn.execute(text("SELECT version_num FROM alembic_version"))).scalar()
                        alt_tables = [r[0] for r in (await alt_conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"))).fetchall()]
                        postgres_db_info = {
                            "has_institutions": alt_inst,
                            "has_user_sessions": alt_sess,
                            "alembic_version": alt_alembic_rev,
                            "tables_count": len(alt_tables),
                            "tables_sample": alt_tables[:10],
                        }
                    await alt_engine.dispose()
                except Exception as alt_err:
                    postgres_db_info = {"error": str(alt_err)}

            raw_host = async_engine.url.host or "unknown"
            port = async_engine.url.port or 5432
            if ".proxy.rlwy.net" in raw_host:
                parts = raw_host.split(".")
                sanitized_server = f"{parts[0][:4]}***.{'.'.join(parts[1:])}:{port}"
            else:
                sanitized_server = f"{raw_host}:{port}"

        return {
            "status": "healthy",
            "database": "postgresql",
            "connected": True,
            "database_name": current_db,
            "available_databases": available_dbs,
            "current_schema": current_schema,
            "available_schemas": available_schemas,
            "search_path": search_path,
            "has_institutions": has_inst_public or has_inst_any,
            "has_user_sessions": has_sess_public or has_sess_any,
            "to_regclass_institutions_public": has_inst_public,
            "to_regclass_user_sessions_public": has_sess_public,
            "alembic_version": alembic_rev,
            "public_tables_count": len(all_tables),
            "public_tables_sample": all_tables[:10],
            "database_postgres_companion": postgres_db_info,
            "sanitized_server": sanitized_server,
        }
    except Exception as exc:
        logger.warning(f"Database health check failed (PostgreSQL not connected): {exc}")
        return {
            "status": "unhealthy",
            "database": "postgresql",
            "connected": False,
            "error": str(exc),
        }
