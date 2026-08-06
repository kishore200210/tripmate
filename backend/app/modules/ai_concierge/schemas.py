"""
app/modules/ai_concierge/schemas.py

Pydantic v2 schemas for the AI Concierge module.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.ai_concierge.enums import MessageRole


class ChatMessageRequest(BaseModel):
    """Schema for POST /api/v1/ai/sessions/{session_id}/stream"""
    content: str = Field(..., min_length=1, max_length=5000, description="The user's message")


class ChatMessageResponse(BaseModel):
    """Safe representation of a ChatMessage."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID | None
    role: MessageRole
    content: str
