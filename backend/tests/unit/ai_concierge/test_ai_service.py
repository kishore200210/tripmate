"""
tests/unit/ai_concierge/test_ai_service.py

Unit tests for AIConciergeService with mocked OpenAI client.
"""

import uuid
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

import app.db.model_registry  # noqa: F401
from app.modules.ai_concierge.enums import MessageRole
from app.modules.ai_concierge.models import ChatMessage
from app.modules.ai_concierge.repository import ChatMessageRepository
from app.modules.ai_concierge.schemas import ChatMessageRequest
from app.modules.ai_concierge.service import AIConciergeService, SYSTEM_PROMPT
from app.modules.users.models import User


@pytest.fixture
def mock_message_repository() -> AsyncMock:
    return AsyncMock(spec=ChatMessageRepository)


@pytest.fixture
def ai_service(
    mock_message_repository: AsyncMock
) -> AIConciergeService:
    # Patch AsyncOpenAI internally so it doesn't try to connect
    with patch("app.modules.ai_concierge.service.AsyncOpenAI") as mock_openai_cls:
        # Create a mock instance
        mock_openai_instance = MagicMock()
        mock_openai_cls.return_value = mock_openai_instance
        
        service = AIConciergeService(
            repository=mock_message_repository,
        )
        return service


@pytest.fixture
def sample_user() -> User:
    user = User()
    user.id = uuid.uuid4()
    return user


class TestAIServiceStream:
    @pytest.mark.asyncio
    async def test_stream_chat_success(
        self,
        ai_service: AIConciergeService,
        mock_message_repository: AsyncMock,
        sample_user: User,
    ) -> None:
        mock_message_repository.get_session_messages.return_value = []
        session_id = uuid.uuid4()
        
        # Setup mock stream for OpenAI
        # Async generator returning chunks
        async def mock_stream():
            class MockChoice:
                def __init__(self, content):
                    self.delta = MagicMock()
                    self.delta.content = content
            
            class MockChunk:
                def __init__(self, content):
                    self.choices = [MockChoice(content)]
                    
            yield MockChunk("Hello ")
            yield MockChunk("World!")
            
        ai_service.openai_client.chat.completions.create = AsyncMock(return_value=mock_stream())

        payload = ChatMessageRequest(content="Hi there!")
        
        chunks = []
        async for chunk in ai_service.stream_chat(session_id, payload, sample_user):
            chunks.append(chunk)
            
        assert chunks == ["Hello ", "World!"]
        
        # Verify user message and AI message were saved
        assert mock_message_repository.create.call_count == 2 # 1 for user, 1 for AI

    @pytest.mark.asyncio
    async def test_get_session_messages(
        self,
        ai_service: AIConciergeService,
        mock_message_repository: AsyncMock,
        sample_user: User,
    ) -> None:
        session_id = uuid.uuid4()
        message = ChatMessage(
            id=uuid.uuid4(),
            user_id=sample_user.id,
            session_id=session_id,
            role=MessageRole.USER,
            content="Hello"
        )
        mock_message_repository.get_session_messages.return_value = [message]

        result = await ai_service.get_session_messages(session_id, sample_user)
        assert len(result) == 1
        assert result[0].content == "Hello"
