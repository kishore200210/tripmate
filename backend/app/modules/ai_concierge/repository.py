"""
app/modules/ai_concierge/repository.py

Repository for AI Concierge models: ChatMessage.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai_concierge.models import ChatMessage
from app.shared.repository import BaseRepository

logger = logging.getLogger(__name__)


class ChatMessageRepository(BaseRepository[ChatMessage]):
    """Repository for ChatMessage database queries."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=ChatMessage, db=db)

    async def get_session_messages(self, session_id: UUID, user_id: UUID) -> list[ChatMessage]:
        """Fetch all messages for a specific session ordered chronologically, ensuring ownership."""
        stmt = (
            select(ChatMessage)
            .where(
                ChatMessage.session_id == session_id,
                ChatMessage.user_id == user_id,
            )
            .order_by(ChatMessage.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
