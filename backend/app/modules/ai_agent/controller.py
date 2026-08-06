"""
app/modules/ai_agent/controller.py

AI Agent Controller — HTTP translation layer for the Agent service.
"""

from uuid import UUID

from app.modules.ai_agent.schemas import AgentChatRequest, AgentChatResponse
from app.modules.ai_agent.service import AIAgentService
from app.modules.users.models import User


class AIAgentController:
    """HTTP controller for the AI Agent module."""

    @staticmethod
    async def chat(
        session_id: UUID, payload: AgentChatRequest, service: AIAgentService, current_user: User
    ) -> AgentChatResponse:
        return await service.chat(session_id, payload, current_user)
