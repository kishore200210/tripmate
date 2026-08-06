"""
tests/unit/ai_agent/test_agent_service.py

Unit tests for AIAgentService with mocked LangGraph invocation.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage

import app.db.model_registry  # noqa: F401
from app.modules.ai_agent.schemas import AgentChatRequest
from app.modules.ai_agent.service import AIAgentService
from app.modules.ai_concierge.repository import ChatMessageRepository
from app.modules.users.enums import UserRole
from app.modules.users.models import User


@pytest.fixture
def mock_message_repository() -> AsyncMock:
    return AsyncMock(spec=ChatMessageRepository)


@pytest.fixture
def agent_service(
    mock_message_repository: AsyncMock
) -> AIAgentService:
    return AIAgentService(repository=mock_message_repository)


@pytest.fixture
def sample_user() -> User:
    user = User()
    user.id = uuid.uuid4()
    user.role = UserRole.USER
    return user


class TestAIAgentServiceChat:
    @pytest.mark.asyncio
    @patch("app.modules.ai_agent.service.compiled_graph")
    async def test_chat_success(
        self,
        mock_graph: AsyncMock,
        agent_service: AIAgentService,
        mock_message_repository: AsyncMock,
        sample_user: User,
    ) -> None:
        mock_message_repository.get_session_messages.return_value = []
        
        # Mock final state returned by ainvoke
        final_state = {
            "messages": [AIMessage(content="The weather in Paris is sunny.")]
        }
        mock_graph.ainvoke = AsyncMock(return_value=final_state)

        session_id = uuid.uuid4()
        payload = AgentChatRequest(message="What's the weather in Paris?")

        result = await agent_service.chat(session_id, payload, sample_user)
        
        assert result.response == "The weather in Paris is sunny."
        assert mock_message_repository.create.call_count == 2 # 1 User msg, 1 AI msg
        
    @pytest.mark.asyncio
    @patch("app.modules.ai_agent.service.compiled_graph")
    async def test_chat_error_fallback(
        self,
        mock_graph: AsyncMock,
        agent_service: AIAgentService,
        mock_message_repository: AsyncMock,
        sample_user: User,
    ) -> None:
        mock_message_repository.get_session_messages.return_value = []
        
        # Simulate LangGraph throwing an error
        mock_graph.ainvoke.side_effect = Exception("API Error")

        session_id = uuid.uuid4()
        payload = AgentChatRequest(message="What's the weather in Paris?")

        result = await agent_service.chat(session_id, payload, sample_user)
        
        assert "encountered an error" in result.response
        assert mock_message_repository.create.call_count == 2
