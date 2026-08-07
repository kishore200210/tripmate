"""
app/modules/rag/service.py

RAG Service — handles Markdown loading, chunking, OpenAI embeddings, and search.
"""

import logging
import os
import uuid
from typing import Any
from uuid import UUID

from app.core.embeddings import EmbeddingService
from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.modules.destinations.models import Document
from app.modules.destinations.repository import DestinationRepository
from app.modules.rag.repository import DocumentRepository
from app.modules.rag.schemas import IngestRequest, SearchRequest, SearchResult
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from app.shared.service import BaseService

logger = logging.getLogger(__name__)


class RAGService(BaseService[DocumentRepository]):
    """Service layer for RAG operations."""

    def __init__(
        self,
        repository: DocumentRepository,
        destination_repository: DestinationRepository,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        super().__init__(repository=repository)
        self.destination_repository = destination_repository
        self.embedding_service = embedding_service or EmbeddingService()

    @property
    def openai_client(self):
        return self.embedding_service.client

    def _chunk_markdown(self, content: str, max_chunk_size: int = 1500) -> list[str]:
        """
        A naive but effective markdown chunker.
        Splits by double newlines (paragraphs) and groups them up to max_chunk_size chars.
        """
        paragraphs = content.split("\n\n")
        chunks = []
        current_chunk = ""

        for p in paragraphs:
            # If a single paragraph is too large, just add it as is (could be improved with sentence splitting)
            if len(p) > max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                chunks.append(p.strip())
                continue

            if len(current_chunk) + len(p) + 2 > max_chunk_size:
                chunks.append(current_chunk.strip())
                current_chunk = p
            else:
                current_chunk += "\n\n" + p if current_chunk else p

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    async def _generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Call EmbeddingService to generate embeddings in batches."""
        return await self.embedding_service.generate_embeddings(texts)

    async def ingest_markdown(self, payload: IngestRequest, current_user: User) -> dict[str, Any]:
        """Ingest a Markdown file, chunk it, embed it, and save to DB."""
        if current_user.role != UserRole.ADMIN:
            raise ResourceNotFoundException("Only admins can ingest documents.")

        dest = await self.destination_repository.get_by_id(payload.destination_id)
        if not dest or dest.is_deleted:
            raise ResourceNotFoundException("Destination not found.")

        # 1. Read file
        if not os.path.exists(payload.file_path):
            raise ValidationException("File path does not exist.")

        with open(payload.file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 2. Chunk content
        chunks = self._chunk_markdown(content)
        if not chunks:
            raise ValidationException("File is empty or could not be chunked.")

        # 3. Generate embeddings
        # OpenAI max batch size is typically 2048, but we'll process in one go for typical files
        embeddings = await self._generate_embeddings(chunks)

        # 4. Clean old chunks for idempotency
        filename = os.path.basename(payload.file_path)
        await self.repository.delete_source_documents(payload.destination_id, filename)

        # 5. Save to DB
        for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            doc = Document(
                id=uuid.uuid4(),
                title=f"{filename} - Part {i+1}",
                content=chunk_text,
                source_file=filename,
                chunk_index=i,
                embedding=embedding,
                destination_id=payload.destination_id,
            )
            # Add to session (BaseRepository.create calls db.add)
            await self.repository.create(doc, commit=False)

        await self.repository.db.commit()

        return {
            "message": "Ingestion successful",
            "chunks_processed": len(chunks),
            "source_file": filename
        }

    async def search(self, payload: SearchRequest) -> list[SearchResult]:
        """Generate embedding for query and perform vector search."""
        dest = await self.destination_repository.get_by_id(payload.destination_id)
        if not dest or dest.is_deleted:
            raise ResourceNotFoundException("Destination not found.")

        # 1. Embed query
        query_embedding_list = await self._generate_embeddings([payload.query])
        if not query_embedding_list:
            return []
        query_embedding = query_embedding_list[0]

        # 2. Perform search via pgvector
        results = await self.repository.similarity_search(
            query_embedding=query_embedding,
            destination_id=payload.destination_id,
            limit=payload.limit
        )

        # 3. Format results with citations
        search_results = []
        for doc, distance in results:
            search_results.append(
                SearchResult(
                    document_id=doc.id,
                    title=doc.title,
                    content=doc.content,
                    source_file=doc.source_file,
                    chunk_index=doc.chunk_index,
                    score=round(distance, 4)  # L2 distance (lower is better)
                )
            )

        return search_results
