"""
app/modules/ai_concierge/router.py

HTTP Routing Layer — AI Concierge Module.

Responsibility:
    - Routes for the AI chat, RAG Q&A, and agent tool invocations.
    - All endpoints require JWT authentication.
    - AI endpoints are rate-limited (AI_RATE_LIMIT_PER_MINUTE).
    - Prefixed /api/v1/ai.

MVC Role: Routing Layer.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/ai", tags=["AI Concierge"])

# Routes will be implemented in Milestone 5 (AI Concierge).
