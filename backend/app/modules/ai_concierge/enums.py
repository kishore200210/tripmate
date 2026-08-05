"""
app/modules/ai_concierge/enums.py

Domain enums for the AI Concierge module.

Why separate from models.py:
    - MessageRole is used by models, schemas, AND the AI service layer.
    - Prevents circular imports.
"""

import enum


class MessageRole(str, enum.Enum):
    """
    The role of the message sender.
    Follows the OpenAI Chat Completions API convention.

    USER: Message from the human traveller.
    ASSISTANT: Response from the AI concierge.
    TOOL: Output from a LangGraph tool/agent call.
    """

    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
