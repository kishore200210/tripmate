"""
app/modules/ai_concierge/models.py

SQLAlchemy ORM model for ChatMessage — the AI conversation memory store.

Technologies: SQLAlchemy 2.x, PostgreSQL.

Architecture:
    - ChatMessage persists each turn of the AI Concierge conversation.
    - role distinguishes user messages from AI assistant responses.
    - session_id groups messages into distinct conversation sessions.
      This enables multi-trip chat isolation (e.g., "Bali trip" vs. "Paris trip").
    - The AI service reads the last N messages PER SESSION to build the LLM
      context window (bounded by tiktoken to prevent token overflow).

Data Model:
    User (1) ──< ChatMessage (many)

Relationships use lazy="raise" (required for async SQLAlchemy).
"""

import uuid

from sqlalchemy import Enum as SAEnum, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.modules.ai_concierge.enums import MessageRole

__all__ = ["ChatMessage"]


class ChatMessage(Base, TimestampMixin):
    """
    A single message in the AI Concierge conversation thread.

    DB Design Notes:
        - No soft-delete: chat history is an immutable audit trail.
          Deleting messages would corrupt the AI's conversation context.
        - session_id: Groups messages into isolated sessions (one per trip or topic).
          Stored as UUID (client-generated or server-generated per session start).
        - token_count: Optional field to track LLM token usage per message.
          Used by the AI service to enforce context window limits without
          re-tokenising on every request.

    Indexes:
        - idx_chat_messages_user_session: Composite index — fetch all messages
          for a specific user + session. Most common AI concierge query.
        - created_at: Indexed (from TimestampMixin) for chronological ordering.
    """

    __tablename__ = "chat_messages"

    __table_args__ = (
        # Composite index: the primary access pattern for chat history retrieval.
        Index("idx_chat_messages_user_session", "user_id", "session_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # MessageRole follows the OpenAI Chat Completions API convention.
    role: Mapped[MessageRole] = mapped_column(
        SAEnum(MessageRole, name="message_role", create_constraint=True),
        nullable=False,
    )

    # The raw text content of the message.
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Optional: tracks LLM token count for context window management.
    # Populated by the AI service using tiktoken after each message.
    token_count: Mapped[int | None] = mapped_column(
        # SmallInteger sufficient for typical message token counts (< 32,767)
        # but Integer is safer for very long tool output messages.
        nullable=True,
        default=None,
    )

    # session_id: Groups messages into a single conversation session.
    # Allows users to have separate AI chats for separate trips.
    # Can be trip_id (UUID of the trip being discussed) or a standalone session UUID.
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    # ── Foreign Keys ──────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Relationships ──────────────────────────────────────
    user: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="chat_messages", lazy="raise"
    )

    def __repr__(self) -> str:
        return (
            f"<ChatMessage id={self.id} role={self.role.value} "
            f"session={self.session_id} user={self.user_id}>"
        )
