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
from app.modules.rag.controller import RAGController
from app.modules.rag.repository import DocumentRepository
from app.modules.rag.schemas import IngestRequest, SearchRequest, SearchResult
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
    "/ingest",
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a Markdown file into the vector database",
)
async def ingest_markdown(
    payload: IngestRequest,
    current_user: User = Depends(get_current_user),
    service: RAGService = Depends(get_rag_service),
) -> dict[str, Any]:
    """
    Reads a Markdown file, chunks it, generates embeddings via OpenAI,
    and saves the chunks to the database using pgvector.
    Requires ADMIN role.
    """
    return await RAGController.ingest_markdown(payload, service, current_user)


@router.post(
    "/search",
    response_model=list[SearchResult],
    summary="Perform a similarity search on the knowledge base",
)
async def search(
    payload: SearchRequest,
    service: RAGService = Depends(get_rag_service),
    # Search can be public or authenticated, depending on product rules.
    # For now, we'll keep it public or optionally protected. Let's make it public.
) -> list[SearchResult]:
    """
    Takes a query, generates an embedding, and performs a pgvector L2 distance search.
    Returns the most relevant chunks with citations.
    """
    return await RAGController.search(payload, service)
