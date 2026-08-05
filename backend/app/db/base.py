"""
app/db/base.py

SQLAlchemy Declarative Base and shared abstract model mixins.

Architecture:
    - All SQLAlchemy models must inherit from Base (for Alembic discovery).
    - TimestampMixin adds created_at / updated_at to every model automatically.
    - SoftDeleteMixin adds is_deleted / deleted_at for safe logical deletion.
    - UUIDs are used as primary keys to prevent sequential enumeration attacks.

Engineering Principles:
    - DRY: Common columns (timestamps, soft-delete) defined ONCE in mixins.
    - Single Responsibility: base.py manages ORM metadata ONLY.

IMPORTANT: Import ALL models in app/db/model_registry.py so Alembic detects them.

SQLAlchemy Best Practices applied:
    - Mixins declare __abstract__ = True so they are never mapped to a table.
    - server_default=func.now() ensures the DB sets timestamps (not Python).
    - All timestamps use timezone=True to store timezone-aware UTC datetimes.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Centralised SQLAlchemy Declarative Base.
    Every ORM model must inherit from this class for Alembic autogenerate to work.
    """

    pass


class TimestampMixin:
    """
    Mixin that adds automatic created_at and updated_at timestamps to every model.

    Best Practices:
        - server_default: the DATABASE sets these values, not Python.
          This is correct even under high-concurrency or clock-skew scenarios.
        - timezone=True: stored as TIMESTAMPTZ in PostgreSQL (UTC-aware).
        - __abstract__ = True: prevents SQLAlchemy from trying to map this as a table.
    """

    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,  # Indexed for chronological ordering queries
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """
    Mixin that adds soft-delete capability to a model.

    Records are NEVER physically deleted — is_deleted is set to True instead.
    This preserves all history for audit, analytics, and data recovery purposes.

    Best Practices:
        - __abstract__ = True: prevents SQLAlchemy from treating this as a table.
        - is_deleted is always indexed — it appears in nearly every WHERE clause.
        - Repositories must filter WHERE is_deleted = FALSE by default.
    """

    __abstract__ = True

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        index=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def soft_delete(self) -> None:
        """
        Mark the record as logically deleted.
        Always use this method instead of setting is_deleted directly.
        """
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Restore a previously soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
