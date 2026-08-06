"""
app/modules/rag/controller.py

RAG Controller — HTTP translation layer for the RAG service.
"""

from typing import Any

from app.modules.rag.schemas import IngestRequest, SearchRequest, SearchResult
from app.modules.rag.service import RAGService
from app.modules.users.models import User


class RAGController:
    """HTTP controller for the RAG module."""

    @staticmethod
    async def ingest_markdown(
        payload: IngestRequest, service: RAGService, current_user: User
    ) -> dict[str, Any]:
        return await service.ingest_markdown(payload, current_user)

    @staticmethod
    async def search(
        payload: SearchRequest, service: RAGService
    ) -> list[SearchResult]:
        return await service.search(payload)
