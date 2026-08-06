"""
app/modules/ai_concierge/router.py

AI Concierge API Router — URL mapping and Swagger documentation.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.ai_concierge.controller import AIConciergeController
from app.modules.ai_concierge.repository import ChatMessageRepository
from app.modules.ai_concierge.schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
)
from app.modules.ai_concierge.service import AIConciergeService
from app.modules.auth.middleware import get_current_user
from app.modules.users.models import User

router = APIRouter(
    prefix="/ai/sessions",
    tags=["AI Concierge"],
)


# ── Dependency Factory ────────────────────────────────────────────────────────

def get_ai_service(db: AsyncSession = Depends(get_db)) -> AIConciergeService:
    message_repo = ChatMessageRepository(db=db)
    return AIConciergeService(repository=message_repo)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/{session_id}/messages",
    response_model=list[ChatMessageResponse],
    summary="Get all messages for a specific chat session",
)
async def get_session_messages(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AIConciergeService = Depends(get_ai_service),
) -> list[ChatMessageResponse]:
    return await AIConciergeController.get_session_messages(session_id, service, current_user)


@router.post(
    "/{session_id}/stream",
    summary="Send a message and stream AI response",
)
async def stream_chat(
    session_id: UUID,
    payload: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    service: AIConciergeService = Depends(get_ai_service),
):
    """
    Takes user input, saves it, and streams back the AI's response chunks.
    This endpoint does NOT return JSON, it returns `text/plain` via Server-Sent-like stream.
    """
    return await AIConciergeController.stream_chat(session_id, payload, service, current_user)
