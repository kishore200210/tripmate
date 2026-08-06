"""
app/modules/ai_agent/router.py

AI Agent API Router — URL mapping and Swagger documentation.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.ai_agent.controller import AIAgentController
from app.modules.ai_agent.schemas import AgentChatRequest, AgentChatResponse
from app.modules.ai_agent.service import AIAgentService
from app.modules.ai_concierge.repository import ChatMessageRepository
from app.modules.auth.middleware import get_current_user
from app.modules.users.models import User

router = APIRouter(
    prefix="/ai/agent",
    tags=["AI Agent"],
)


# ── Dependency Factory ────────────────────────────────────────────────────────

def get_ai_agent_service(db: AsyncSession = Depends(get_db)) -> AIAgentService:
    repository = ChatMessageRepository(db=db)
    return AIAgentService(repository=repository)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/{session_id}/chat",
    response_model=AgentChatResponse,
    summary="Chat with the LangGraph AI Agent",
)
async def chat(
    session_id: UUID,
    payload: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    service: AIAgentService = Depends(get_ai_agent_service),
) -> AgentChatResponse:
    """
    Takes a user message, fetches session history, and invokes the LangGraph AI Agent.
    The Agent has access to Weather and Currency tools.
    """
    return await AIAgentController.chat(session_id, payload, service, current_user)
