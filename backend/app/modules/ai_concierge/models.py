"""
app/modules/ai_concierge/models.py

SQLAlchemy ORM model for ChatMessage — the AI conversation memory store.

Technologies: SQLAlchemy, PostgreSQL.

Architecture:
    - ChatMessage persists each turn of the conversation between user and AI.
    - The role field distinguishes user messages from AI assistant responses.
    - The AI service reads the last N messages to build the conversation history
      context window sent to the LLM (bounded by tiktoken to avoid token overflow).

Data Model:
    ChatMessage belongs to User
"""

import uuid

from sqlalchemy import Enum as SAEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.base import Base, TimestampMixin


class MessageRole(str, enum.Enum):
    """
    The role of the message sender, following the OpenAI Chat Completions API convention.

    USER: Message from the human traveller.
    ASSISTANT: Response from the AI concierge (LLM).
    SYSTEM: System-level prompt injected at the start of a conversation (not stored).
    TOOL: Output from a tool/agent call (e.g. weather fetch result).
    """

    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ChatMessage(Base, TimestampMixin):
    """
    A single message in the AI Concierge conversation thread.

    Note:
        - Messages are NEVER soft-deleted — the full history is an audit trail.
        - The context window sent to the LLM is capped at the last N messages
          by the AI service layer (not at the database level).

    Indexes:
        - user_id: For fetching conversation history for a specific user.
        - created_at: For ordering messages chronologically.
    """

    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    role: Mapped[MessageRole] = mapped_column(
        SAEnum(MessageRole, name="message_role"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Foreign Keys ───────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Relationships ───────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="chat_messages")  # noqa: F821

    def __repr__(self) -> str:
        return f"<ChatMessage id={self.id} role={self.role} user={self.user_id}>"
