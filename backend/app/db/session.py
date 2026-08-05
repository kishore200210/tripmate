"""
app/db/session.py

Async database engine and session factory.

Technologies Used:
    - SQLAlchemy[asyncio]: Async ORM engine
    - psycopg: Modern async PostgreSQL driver (psycopg v3)
    - pydantic-settings: For reading DATABASE_URL from config

Architecture:
    - create_async_engine creates a single shared engine (connection pool).
    - AsyncSessionLocal is the session factory used to create DB sessions.
    - get_db() is a FastAPI dependency that yields a session and closes it cleanly.

Engineering Principles:
    - Dependency Injection: get_db() is injected into Repositories via Depends().
    - Single Responsibility: session.py ONLY manages DB connection lifecycle.
    - Never import get_db() directly in Services — always inject via Repositories.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

settings = get_settings()

# ── Engine ────────────────────────────────────────────────
# Single shared engine instance with connection pooling.
# pool_pre_ping ensures stale connections are removed before use.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,          # Log SQL in development only
    pool_pre_ping=True,           # Validate connection health
    pool_size=10,                 # Max persistent connections
    max_overflow=20,              # Max extra connections under load
)

# ── Session Factory ───────────────────────────────────────
# expire_on_commit=False prevents attribute access errors after commit
# in async context (since lazy loading is not supported in async SQLAlchemy).
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── FastAPI Dependency ────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session per request.

    Usage in a Router:
        @router.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            ...

    The session is always closed after the request, even if an exception occurs.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
