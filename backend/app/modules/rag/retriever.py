"""
app/modules/rag/retriever.py

Retrieval logic for the RAG module.
"""

from typing import Any
from uuid import UUID
from app.modules.rag.repository import DocumentRepository
from app.core.embeddings import EmbeddingService

class RAGRetriever:
    """Handles vector search and context formatting."""

    def __init__(self, repository: DocumentRepository, embedding_service: EmbeddingService):
        self.repository = repository
        self.embedding_service = embedding_service

    async def retrieve_context(self, query: str, limit: int = 5) -> dict[str, Any]:
        """
        Embeds the query, searches for relevant documents globally,
        and formats them into a context string and a list of sources.
        """
        query_embedding = await self.embedding_service.generate_embedding(query)
        if not query_embedding:
            return {"context": "", "sources": []}

        # Global search (destination_id = None)
        results = await self.repository.similarity_search(
            query_embedding=query_embedding,
            destination_id=None,
            limit=limit
        )

        sources = set()
        context_blocks = []

        for doc, distance in results:
            if doc.source_file:
                sources.add(doc.source_file)
            context_blocks.append(f"Source: {doc.source_file}\nContent:\n{doc.content}")

        return {
            "context": "\n\n---\n\n".join(context_blocks),
            "sources": list(sources)
        }
