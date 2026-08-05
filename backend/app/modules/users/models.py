"""
app/modules/users/models.py

SQLAlchemy ORM model for the User entity.

Technologies: SQLAlchemy 2.x, PostgreSQL, UUID primary keys.

Architecture:
    - User is the root aggregate for identity and authentication.
    - Password is NEVER stored in plain text — only the Argon2id hash.
    - RBAC is enforced via the UserRole enum (USER | ADMIN).
    - Soft-delete preserves user data for audit and recovery.

Data Model:
    User (1) ──< Trip (many)
    User (1) ──< Review (many)
    User (1) ──< ChatMessage (many)

Relationships use lazy="raise" to enforce explicit loading in async context.
    In async SQLAlchemy, lazy="select" causes MissingGreenlet errors.
    Use lazy="raise" + selectinload() or joinedload() in repositories.
"""

import uuid

from sqlalchemy import Boolean, Enum as SAEnum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, SoftDeleteMixin
from app.modules.users.enums import UserRole

__all__ = ["User"]


class User(Base, TimestampMixin, SoftDeleteMixin):
    """
    User entity — the central identity model for TripMate.

    DB Constraints:
        - email: UNIQUE + NOT NULL (enforced at DB level)
        - password_hash: String(1024) — Argon2id hashes can be long
        - role: DEFAULT 'user' (DB-level default)
        - is_active: DEFAULT TRUE

    Indexes:
        - email: Unique index — fast login lookup.
        - role: Index — fast admin-only dashboard queries.
        - is_deleted + is_active: From mixins — soft-delete and account status filtering.
    """

    __tablename__ = "users"

    # ── Primary Key ────────────────────────────────────────
    # Note: primary_key columns are automatically indexed by PostgreSQL.
    # The index=True flag is redundant on PKs and intentionally omitted.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ── Identity Fields ────────────────────────────────────
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,  # Fast login lookup — most queried field
    )

    # ── Security ───────────────────────────────────────────
    # Argon2id hashes are typically 95-120 chars but can exceed 255.
    # String(1024) gives significant headroom for any future algorithm change.
    # NEVER log, return, or compare this field directly — use security.verify_password().
    password_hash: Mapped[str] = mapped_column(String(1024), nullable=False)

    # ── RBAC ──────────────────────────────────────────────
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", create_constraint=True),
        default=UserRole.USER,
        server_default=UserRole.USER.value,  # DB-level default
        nullable=False,
        index=True,
    )

    # ── Account Status ─────────────────────────────────────
    # is_active: Can be set to False to disable login without deleting the account.
    # Separate from soft-delete: a user can be deactivated but not deleted.
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",  # DB-level default
        nullable=False,
        index=True,
    )

    # ── Relationships ──────────────────────────────────────
    # lazy="raise" is correct for async SQLAlchemy.
    # Repositories must use selectinload() or joinedload() explicitly.
    trips: Mapped[list["Trip"]] = relationship(  # noqa: F821
        "Trip",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="raise",
        passive_deletes=True,
    )
    reviews: Mapped[list["Review"]] = relationship(  # noqa: F821
        "Review",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="raise",
        passive_deletes=True,
    )
    chat_messages: Mapped[list["ChatMessage"]] = relationship(  # noqa: F821
        "ChatMessage",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="raise",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role.value}>"
