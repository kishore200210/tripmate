"""
app/modules/rag/router.py

RAG API Router — URL mapping and Swagger documentation.
"""

from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.middleware import get_current_user
from app.modules.destinations.repository import DestinationRepository

from app.modules.rag.repository import DocumentRepository
from app.modules.rag.schemas import RAGQueryRequest, RAGQueryResponse
from app.modules.rag.service import RAGService
from app.modules.users.models import User

router = APIRouter(
    prefix="/rag",
    tags=["RAG Knowledge Base"],
)


# ── Dependency Factory ────────────────────────────────────────────────────────

def get_rag_service(db: AsyncSession = Depends(get_db)) -> RAGService:
    repository = DocumentRepository(db=db)
    destination_repository = DestinationRepository(db=db)
    return RAGService(repository=repository, destination_repository=destination_repository)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/query",
    response_model=RAGQueryResponse,
    summary="Query the travel knowledge base",
)
async def query_knowledge_base(
    payload: RAGQueryRequest,
    service: RAGService = Depends(get_rag_service),
) -> RAGQueryResponse:
    """
    RAG pipeline: Embeds the query, retrieves chunks, formats context, and returns LLM generated answer with citations.
    """
    return await service.query_knowledge_base(payload)


@router.post(
    "/reindex",
    status_code=status.HTTP_200_OK,
    summary="Reindex all travel documents",
)
async def reindex_documents(
    current_user: User = Depends(get_current_user),
    service: RAGService = Depends(get_rag_service),
) -> dict[str, Any]:
    """
    Reads all documents from backend/travel_docs/, generates embeddings, and saves to pgvector.
    Requires authentication (ideally admin, but limited to logged-in users here for simplicity).
    """
    return await service.reindex_all_documents()


@router.get(
    "/status",
    summary="Get RAG index status",
)
async def get_status(
    service: RAGService = Depends(get_rag_service),
) -> dict[str, Any]:
    """
    Returns the total number of chunks currently indexed in the vector DB.
    """
    return await service.get_status()
