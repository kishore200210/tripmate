"""
tests/unit/rag/test_rag_service.py

Unit tests for the new RAGService implementation.
"""
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
import pytest

from app.modules.destinations.models import Destination
from app.modules.destinations.repository import DestinationRepository
from app.modules.rag.repository import DocumentRepository
from app.modules.rag.schemas import RAGQueryRequest, RAGQueryResponse
from app.modules.rag.service import RAGService


@pytest.fixture
def mock_document_repository() -> AsyncMock:
    repo = AsyncMock(spec=DocumentRepository)
    repo.db = AsyncMock() # Mock the db session
    return repo


@pytest.fixture
def mock_dest_repository() -> AsyncMock:
    return AsyncMock(spec=DestinationRepository)


@pytest.fixture
def rag_service(
    mock_document_repository: AsyncMock, mock_dest_repository: AsyncMock
) -> RAGService:
    service = RAGService(
        repository=mock_document_repository,
        destination_repository=mock_dest_repository,
    )
    # Mock groq client
    service.groq_client = AsyncMock()
    # Mock embeddings
    service.embedding_service = AsyncMock()
    # Mock retriever
    service.retriever = AsyncMock()
    return service


class TestRAGService:
    @pytest.mark.asyncio
    async def test_query_knowledge_base_success(
        self,
        rag_service: RAGService,
    ) -> None:
        # Mock retriever response
        rag_service.retriever.retrieve_context.return_value = {
            "context": "Paris has the Eiffel Tower.",
            "sources": ["paris_guide.txt"]
        }
        
        # Mock Groq
        class MockMessage:
            content = "The Eiffel Tower is in Paris."
        class MockChoice:
            message = MockMessage()
        class MockGroqResponse:
            choices = [MockChoice()]
            
        rag_service.groq_client.chat.completions.create.return_value = MockGroqResponse()
        
        payload = RAGQueryRequest(query="What is in Paris?")
        result = await rag_service.query_knowledge_base(payload)
        
        assert result.answer == "The Eiffel Tower is in Paris."
        assert "paris_guide.txt" in result.sources

    @pytest.mark.asyncio
    async def test_query_knowledge_base_no_context(
        self,
        rag_service: RAGService,
    ) -> None:
        # Mock retriever response empty
        rag_service.retriever.retrieve_context.return_value = {
            "context": "",
            "sources": []
        }
        
        payload = RAGQueryRequest(query="What is in Paris?")
        result = await rag_service.query_knowledge_base(payload)
        
        assert "I couldn't find any relevant travel documents" in result.answer
        assert len(result.sources) == 0

    @pytest.mark.asyncio
    async def test_get_status(
        self,
        rag_service: RAGService,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar.return_value = 10
        rag_service.repository.db.execute = AsyncMock(return_value=mock_result)
        
        status = await rag_service.get_status()
        assert status["total_chunks"] == 10
