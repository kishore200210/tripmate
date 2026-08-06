"""
app/modules/ai_concierge/controller.py

AI Concierge Controller — HTTP translation layer for the AI service.
"""

from uuid import UUID

from fastapi.responses import StreamingResponse

from app.modules.ai_concierge.schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
)
from app.modules.ai_concierge.service import AIConciergeService
from app.modules.users.models import User


class AIConciergeController:
    """HTTP controller for the AI Concierge module."""

    @staticmethod
    async def get_session_messages(
        session_id: UUID, service: AIConciergeService, current_user: User
    ) -> list[ChatMessageResponse]:
        return await service.get_session_messages(session_id, current_user)

    @staticmethod
    async def stream_chat(
        session_id: UUID, payload: ChatMessageRequest, service: AIConciergeService, current_user: User
    ) -> StreamingResponse:
        """Returns a StreamingResponse yielding chunks from the OpenAI API."""
        return StreamingResponse(
            service.stream_chat(session_id, payload, current_user),
            media_type="text/plain"
        )
