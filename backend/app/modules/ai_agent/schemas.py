"""
app/modules/ai_agent/schemas.py

Pydantic v2 schemas for the AI Agent module.
"""

from pydantic import BaseModel, ConfigDict, Field


class AgentChatRequest(BaseModel):
    """Schema for POST /api/v1/ai/agent/{session_id}/chat"""
    message: str = Field(..., min_length=1, max_length=5000, description="The user's message")


class AgentChatResponse(BaseModel):
    """Safe representation of an Agent's response."""
    model_config = ConfigDict(from_attributes=True)

    response: str = Field(..., description="The AI's formulated response")
