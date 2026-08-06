"""
tests/unit/destinations/test_destination_service.py

Unit tests for DestinationService.
"""

import io
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import UploadFile

# Import model registry for SQLAlchemy mapper
import app.db.model_registry  # noqa: F401
from app.core.exceptions import (
    BusinessRuleViolationException,
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
    ValidationException,
)
from app.modules.destinations.models import Destination
from app.modules.destinations.repository import DestinationRepository
from app.modules.destinations.schemas import (
    DestinationCreateRequest,
    DestinationUpdateRequest,
)
from app.modules.destinations.service import DestinationService


@pytest.fixture
def mock_repository() -> AsyncMock:
    return AsyncMock(spec=DestinationRepository)


@pytest.fixture
def destination_service(mock_repository: AsyncMock) -> DestinationService:
    return DestinationService(repository=mock_repository)


@pytest.fixture
def sample_destination() -> Destination:
    dest = Destination()
    dest.id = uuid.uuid4()
    dest.name = "Paris"
    dest.country = "France"
    dest.description = "City of light."
    dest.avg_budget = Decimal("150.00")
    dest.tags = ["romantic", "history"]
    dest.image_url = None
    dest.is_deleted = False
    return dest


class TestDestinationServiceSearch:
    @pytest.mark.asyncio
    async def test_search_destinations(
        self, destination_service: DestinationService, mock_repository: AsyncMock, sample_destination: Destination
    ) -> None:
        mock_repository.search.return_value = ([sample_destination], 1)

        result = await destination_service.search_destinations(query="Paris")
        
        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].name == "Paris"
        mock_repository.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_destinations_invalid_sort(
        self, destination_service: DestinationService, mock_repository: AsyncMock, sample_destination: Destination
    ) -> None:
        mock_repository.search.return_value = ([sample_destination], 1)

        # Invalid sort_by field should default to "name"
        await destination_service.search_destinations(sort_by="invalid_field")
        
        # Verify it defaulted to 'name'
        mock_repository.search.assert_called_once()
        assert mock_repository.search.call_args.kwargs["sort_by"] == "name"


class TestDestinationServiceGet:
    @pytest.mark.asyncio
    async def test_get_destination_success(
        self, destination_service: DestinationService, mock_repository: AsyncMock, sample_destination: Destination
    ) -> None:
        mock_repository.get_by_id.return_value = sample_destination
        
        result = await destination_service.get_destination(sample_destination.id, is_admin=True)
        assert result.name == "Paris"


class TestDestinationServiceCreate:
    @pytest.mark.asyncio
    async def test_create_destination_success(
        self, destination_service: DestinationService, mock_repository: AsyncMock, sample_destination: Destination
    ) -> None:
        mock_repository.name_exists.return_value = False
        mock_repository.create.return_value = sample_destination

        payload = DestinationCreateRequest(
            name="Paris",
            country="France",
            description="City of light.",
            avg_budget=Decimal("150.00")
        )
        
        result = await destination_service.create_destination(payload)
        
        assert result.name == "Paris"
        mock_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_destination_duplicate_name(
        self, destination_service: DestinationService, mock_repository: AsyncMock
    ) -> None:
        mock_repository.name_exists.return_value = True

        payload = DestinationCreateRequest(
            name="Paris", country="France", description="City of light.", avg_budget=Decimal("150.00")
        )
        
        with pytest.raises(ResourceAlreadyExistsException):
            await destination_service.create_destination(payload)


class TestDestinationServiceUpdate:
    @pytest.mark.asyncio
    async def test_update_destination_success(
        self, destination_service: DestinationService, mock_repository: AsyncMock, sample_destination: Destination
    ) -> None:
        mock_repository.get_by_id.return_value = sample_destination
        mock_repository.name_exists.return_value = False
        mock_repository.update.return_value = sample_destination

        payload = DestinationUpdateRequest(name="New Paris")
        
        result = await destination_service.update_destination(sample_destination.id, payload)
        
        assert sample_destination.name == "New Paris"
        assert result.name == "New Paris"
        mock_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_destination_duplicate_name(
        self, destination_service: DestinationService, mock_repository: AsyncMock, sample_destination: Destination
    ) -> None:
        mock_repository.get_by_id.return_value = sample_destination
        mock_repository.name_exists.return_value = True

        payload = DestinationUpdateRequest(name="London")
        
        with pytest.raises(ResourceAlreadyExistsException):
            await destination_service.update_destination(sample_destination.id, payload)


class TestDestinationServiceUpload:
    @pytest.mark.asyncio
    async def test_upload_image_invalid_extension(
        self, destination_service: DestinationService, mock_repository: AsyncMock, sample_destination: Destination
    ) -> None:
        mock_repository.get_by_id.return_value = sample_destination
        
        # Mock file with invalid extension
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "malicious.exe"
        
        with pytest.raises(ValidationException):
            await destination_service.upload_image(sample_destination.id, mock_file)
