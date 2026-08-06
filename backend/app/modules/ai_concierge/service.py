"""
app/modules/ai_concierge/service.py

AI Concierge Service — business logic and OpenAI integration.
"""

import logging
import os
import uuid
from typing import AsyncGenerator
from uuid import UUID

import tiktoken
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from app.modules.ai_concierge.enums import MessageRole
from app.modules.ai_concierge.models import ChatMessage
from app.modules.ai_concierge.repository import ChatMessageRepository
from app.modules.ai_concierge.schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
)
from app.modules.users.models import User
from app.shared.service import BaseService

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are TripMate's AI Travel Concierge. 
You are an expert travel agent designed to help users plan trips, discover destinations, and build itineraries.
Be polite, engaging, and provide structured, highly relevant travel advice.
If asked about things unrelated to travel, politely guide the conversation back to travel planning.
Keep responses concise but comprehensive."""

OPENAI_MODEL = "gpt-3.5-turbo"
MAX_HISTORY_TOKENS = 2000


class AIConciergeService(BaseService[ChatMessageRepository]):
    """Service layer for AI Concierge operations."""

    def __init__(
        self,
        repository: ChatMessageRepository,
    ) -> None:
        super().__init__(repository=repository)
        self.openai_client = AsyncOpenAI(
            api_key=os.environ.get("OPENAI_API_KEY", "dummy-key-for-tests")
        )

    def _count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken for the target model."""
        try:
            encoding = tiktoken.encoding_for_model(OPENAI_MODEL)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

    async def get_session_messages(
        self, session_id: UUID, current_user: User
    ) -> list[ChatMessageResponse]:
        """Get the full message history for a session."""
        messages = await self.repository.get_session_messages(session_id, current_user.id)
        return [ChatMessageResponse.model_validate(m) for m in messages]

    async def stream_chat(
        self, session_id: UUID, payload: ChatMessageRequest, current_user: User
    ) -> AsyncGenerator[str, None]:
        """Stream a response from OpenAI while maintaining conversation memory."""
        # 1. Save user's message to DB
        user_message = ChatMessage(
            id=uuid.uuid4(),
            user_id=current_user.id,
            session_id=session_id,
            role=MessageRole.USER,
            content=payload.content.strip(),
        )
        await self.repository.create(user_message)

        # 2. Fetch recent history from DB
        all_messages = await self.repository.get_session_messages(session_id, current_user.id)
        
        # 3. Build context and enforce token limits
        context_messages: list[ChatCompletionMessageParam] = []
        current_tokens = self._count_tokens(SYSTEM_PROMPT)

        for msg in reversed(all_messages):
            msg_tokens = self._count_tokens(msg.content)
            if current_tokens + msg_tokens > MAX_HISTORY_TOKENS:
                break
            
            context_messages.insert(0, {"role": msg.role.value, "content": msg.content}) # type: ignore
            current_tokens += msg_tokens

        context_messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

        # 4. Stream response from OpenAI
        ai_full_content = ""
        
        try:
            stream = await self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=context_messages,
                stream=True,
                temperature=0.7,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content is not None:
                    delta_content = chunk.choices[0].delta.content
                    ai_full_content += delta_content
                    yield delta_content
                    
        except Exception as e:
            logger.error("OpenAI Streaming Error: %s", str(e))
            error_msg = "\n\n*Error: The AI Concierge is currently unavailable. Please try again later.*"
            ai_full_content += error_msg
            yield error_msg
            
        finally:
            # 5. Save AI response
            if ai_full_content:
                ai_message = ChatMessage(
                    id=uuid.uuid4(),
                    user_id=current_user.id,
                    session_id=session_id,
                    role=MessageRole.ASSISTANT,
                    content=ai_full_content,
                )
                await self.repository.create(ai_message)
