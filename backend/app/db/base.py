"""
app/db/base.py

SQLAlchemy Declarative Base and shared abstract model mixin.

Architecture:
    - All SQLAlchemy models must inherit from Base (for Alembic discovery).
    - TimestampMixin adds created_at / updated_at to every model automatically.
    - SoftDeleteMixin adds is_deleted / deleted_at for safe record removal.
    - UUIDs are used as primary keys to prevent enumeration attacks.

Engineering Principles:
    - DRY: Common columns (pk, timestamps) defined ONCE in mixins.
    - Single Responsibility: base.py manages ORM metadata only.

IMPORTANT: Import ALL models in alembic/env.py so Alembic can detect them.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, func, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Centralised SQLAlchemy Declarative Base.
    Every ORM model must inherit from this class for Alembic autogenerate to work.
    """

    pass


class TimestampMixin:
    """
    Mixin that adds automatic created_at and updated_at timestamps to a model.
    All timestamps are stored in UTC.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
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
    """

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def soft_delete(self) -> None:
        """Mark the record as deleted without removing it from the database."""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
