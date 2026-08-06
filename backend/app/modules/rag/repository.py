"""
app/modules/rag/repository.py

Document Repository — handles pgvector storage and similarity search.
"""

import logging
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.destinations.models import Document
from app.shared.repository import BaseRepository

logger = logging.getLogger(__name__)


class DocumentRepository(BaseRepository[Document]):
    """Repository for RAG Document database queries including pgvector search."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=Document, db=db)

    async def delete_source_documents(self, destination_id: UUID, source_file: str) -> None:
        """Clear out old chunks for a file before re-ingesting to maintain idempotency."""
        stmt = delete(Document).where(
            Document.destination_id == destination_id,
            Document.source_file == source_file
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def similarity_search(
        self, query_embedding: list[float], destination_id: UUID, limit: int = 5
    ) -> list[tuple[Document, float]]:
        """
        Perform a pgvector similarity search using L2 distance.
        Returns a list of tuples containing (Document, distance_score).
        Lower distance = more similar.
        """
        # Document.embedding.l2_distance(query_embedding) computes the L2 distance
        distance = Document.embedding.l2_distance(query_embedding).label("distance")
        
        stmt = (
            select(Document, distance)
            .where(
                Document.destination_id == destination_id,
                # In production, might filter by threshold, e.g., distance < 1.0
            )
            .order_by(distance)
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        
        # result.all() returns tuples of (Document, float)
        return [(row[0], row[1]) for row in result.all()]
