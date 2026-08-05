"""
tests/conftest.py

Pytest shared fixtures for the TripMate backend test suite.

Architecture:
    - Provides a test database session isolated from the production database.
    - Provides a FastAPI TestClient for integration and E2E tests.
    - All fixtures use function scope to guarantee test isolation.

Environment:
    - Tests use a separate TEST database (set via TEST_DATABASE_URL env var).
    - All test transactions are rolled back after each test — no state leaks.

Technologies: pytest, pytest-asyncio, SQLAlchemy async, FastAPI TestClient.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.session import get_db
from app.main import create_application


# ── Test Database Setup ───────────────────────────────────
# Uses a separate in-process SQLite for unit tests (fast, no Docker needed).
# For integration tests against PostgreSQL, set TEST_DATABASE_URL in the CI env.
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_tables():
    """Create all tables in the test database once per session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncSession:
    """
    Provides a test database session that is rolled back after each test.
    Inject as: async def test_something(db_session: AsyncSession): ...
    """
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncClient:
    """
    Provides an AsyncClient that hits the real FastAPI app with the test DB injected.
    Use for integration and E2E tests.
    Inject as: async def test_endpoint(async_client: AsyncClient): ...
    """
    app = create_application()

    # Override get_db to use the test session
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
