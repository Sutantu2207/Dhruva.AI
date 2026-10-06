"""Pytest configuration and shared fixtures for Dhruva.AI backend tests.

Sets up an isolated async database session per test and provides an authenticated test client.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from app.main import app
from app.core.database import Base
from app.api.deps import get_db

# Isolated test engine using SQLite in-memory for fast, hermetic unit & integration tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session", autouse=True)
def anyio_backend():
    return "asyncio"


from app.domains.identity.rate_limiter import auth_rate_limiter


@pytest.fixture(autouse=True)
async def setup_test_db():
    """Creates database tables before each test and drops them afterwards."""
    auth_rate_limiter._hits.clear()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    auth_rate_limiter._hits.clear()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    """Dependency override providing test session."""
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture
async def db_session():
    """Direct fixture for accessing DB session in tests."""
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
async def async_client():
    """Provides an asynchronous test client for API endpoints."""
    from app.core.database import get_db_session
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_db_session] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.clear()
