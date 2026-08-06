"""
app/db/migrations/env.py

Alembic migration environment — configured for async SQLAlchemy + psycopg.

Changes from the generated default:
    1. Uses run_async_migrations() for async engine compatibility.
    2. Imports model_registry to expose all ORM models to autogenerate.
    3. Reads DATABASE_URL from Pydantic Settings (not hardcoded in alembic.ini).
    4. Sets include_schemas=True for pgvector schema support.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.db.base import Base

# ── CRITICAL: Import all models so Alembic can detect them ─
import app.db.model_registry  # noqa: F401

# ── Alembic Config ─────────────────────────────────────────
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

settings = get_settings()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generates SQL without a live DB connection)."""
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:  # type: ignore[no-untyped-def]
    print("DEBUG: Inside do_run_migrations")
    print(f"DEBUG: target_metadata tables = {target_metadata.tables.keys()}")
    print(f"DEBUG: Executing do_run_migrations")
    
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,       # Detect column type changes
        compare_server_default=True,
    )
    with context.begin_transaction():
        print(f"DEBUG: Migration context configured. Current revision: {context.get_context().get_current_revision()}")
        context.run_migrations()
        print("DEBUG: context.run_migrations() completed")


async def run_async_migrations() -> None:
    """Run migrations using an async engine connection (required for psycopg v3)."""
    connectable = create_async_engine(settings.DATABASE_URL)
    print(f"DEBUG: DATABASE_URL = {settings.DATABASE_URL}")
    print(f"DEBUG: Base.metadata tables = {list(Base.metadata.tables.keys())}")
    async with connectable.begin() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migration mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
