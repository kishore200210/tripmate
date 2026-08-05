"""
app/modules/users/models.py

SQLAlchemy ORM model for the User entity.

Technologies: SQLAlchemy, PostgreSQL, pgvector (n/a here), UUID primary keys.

Architecture:
    - User is the root aggregate for identity and authentication.
    - Password is NEVER stored in plain text — only the Argon2 hash.
    - RBAC is implemented via the UserRole enum (USER | ADMIN).
    - Soft-delete is applied so user data is preserved for audit purposes.

Data Model:
    User has many Trips
    User has many Reviews
    User has many ChatMessages
"""

import uuid

from sqlalchemy import Boolean, Enum as SAEnum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, SoftDeleteMixin
from app.modules.users.enums import UserRole  # Enum defined in enums.py (SRP)

__all__ = ["User"]


class User(Base, TimestampMixin, SoftDeleteMixin):
    """
    User entity — the central identity model for TripMate.

    Indexes:
        - email: Unique index for login lookup.
        - role: Index for admin-only queries.
    """

    __tablename__ = "users"

    # ── Primary Key ───────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # ── Identity Fields ───────────────────────────────────
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,  # Fast login lookup
    )

    # ── Security Fields ───────────────────────────────────
    # NEVER store raw passwords. Only store the Argon2 hash.
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # ── RBAC ─────────────────────────────────────────────
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role"),
        default=UserRole.USER,
        nullable=False,
        index=True,
    )

    # ── Account Status ────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ── Relationships ─────────────────────────────────────
    trips: Mapped[list["Trip"]] = relationship(  # noqa: F821
        "Trip",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )
    reviews: Mapped[list["Review"]] = relationship(  # noqa: F821
        "Review",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )
    chat_messages: Mapped[list["ChatMessage"]] = relationship(  # noqa: F821
        "ChatMessage",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
