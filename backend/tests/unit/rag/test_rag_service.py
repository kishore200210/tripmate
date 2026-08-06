"""
tests/unit/rag/test_rag_service.py

Unit tests for RAGService with mocked OpenAI embeddings.
"""

import os
import uuid
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

import app.db.model_registry  # noqa: F401
from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.modules.destinations.models import Destination, Document
from app.modules.destinations.repository import DestinationRepository
from app.modules.rag.repository import DocumentRepository
from app.modules.rag.schemas import IngestRequest, SearchRequest
from app.modules.rag.service import RAGService
from app.modules.users.enums import UserRole
from app.modules.users.models import User


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
    # Patch AsyncOpenAI internally
    with patch("app.modules.rag.service.AsyncOpenAI") as mock_openai_cls:
        mock_openai_instance = MagicMock()
        mock_openai_cls.return_value = mock_openai_instance
        
        service = RAGService(
            repository=mock_document_repository,
            destination_repository=mock_dest_repository,
        )
        return service


@pytest.fixture
def sample_admin() -> User:
    user = User()
    user.id = uuid.uuid4()
    user.role = UserRole.ADMIN
    return user


@pytest.fixture
def sample_destination() -> Destination:
    dest = Destination()
    dest.id = uuid.uuid4()
    dest.is_deleted = False
    return dest


class TestRAGServiceIngest:
    @pytest.mark.asyncio
    async def test_chunk_markdown_logic(self, rag_service: RAGService) -> None:
        content = "Para 1\n\nPara 2\n\nPara 3"
        chunks = rag_service._chunk_markdown(content, max_chunk_size=10)
        # "Para 1" is 6 chars, "Para 2" is 6 chars, so they split
        assert len(chunks) == 3
        assert chunks[0] == "Para 1"

    @pytest.mark.asyncio
    async def test_ingest_markdown_success(
        self,
        rag_service: RAGService,
        mock_document_repository: AsyncMock,
        mock_dest_repository: AsyncMock,
        sample_admin: User,
        sample_destination: Destination,
        tmp_path,
    ) -> None:
        mock_dest_repository.get_by_id.return_value = sample_destination
        
        # Setup mock file
        file_path = tmp_path / "guide.md"
        file_path.write_text("Hello World!")
        
        # Mock OpenAI embeddings
        class MockData:
            def __init__(self, embedding):
                self.embedding = embedding
                
        class MockResponse:
            def __init__(self):
                self.data = [MockData([0.1, 0.2, 0.3])]
                
        rag_service.openai_client.embeddings.create = AsyncMock(return_value=MockResponse())

        payload = IngestRequest(
            destination_id=sample_destination.id,
            file_path=str(file_path)
        )

        result = await rag_service.ingest_markdown(payload, sample_admin)
        
        assert result["message"] == "Ingestion successful"
        assert result["chunks_processed"] == 1
        assert result["source_file"] == "guide.md"
        
        # Verify db interaction
        mock_document_repository.delete_source_documents.assert_called_once()
        mock_document_repository.create.assert_called_once()
        mock_document_repository.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingest_markdown_unauthorized(
        self,
        rag_service: RAGService,
        sample_destination: Destination,
    ) -> None:
        user = User()
        user.role = UserRole.USER
        
        payload = IngestRequest(
            destination_id=sample_destination.id,
            file_path="dummy.md"
        )
        
        with pytest.raises(ResourceNotFoundException):
            await rag_service.ingest_markdown(payload, user)


class TestRAGServiceSearch:
    @pytest.mark.asyncio
    async def test_search_success(
        self,
        rag_service: RAGService,
        mock_document_repository: AsyncMock,
        mock_dest_repository: AsyncMock,
        sample_destination: Destination,
    ) -> None:
        mock_dest_repository.get_by_id.return_value = sample_destination
        
        # Mock OpenAI embeddings
        class MockData:
            def __init__(self, embedding):
                self.embedding = embedding
                
        class MockResponse:
            def __init__(self):
                self.data = [MockData([0.1, 0.2, 0.3])]
                
        rag_service.openai_client.embeddings.create = AsyncMock(return_value=MockResponse())
        
        # Mock repository search response
        doc = Document()
        doc.id = uuid.uuid4()
        doc.title = "guide.md - Part 1"
        doc.content = "Paris is great"
        doc.source_file = "guide.md"
        doc.chunk_index = 0
        
        mock_document_repository.similarity_search.return_value = [(doc, 0.15)]
        
        payload = SearchRequest(
            destination_id=sample_destination.id,
            query="Paris",
            limit=5
        )
        
        results = await rag_service.search(payload)
        
        assert len(results) == 1
        assert results[0].content == "Paris is great"
        assert results[0].score == 0.15
        mock_document_repository.similarity_search.assert_called_once()
