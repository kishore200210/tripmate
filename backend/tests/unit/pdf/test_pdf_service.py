"""
tests/unit/pdf/test_pdf_service.py

Unit tests for PDFService with mocked Celery task execution.
"""

import uuid
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

import app.db.model_registry  # noqa: F401
from app.modules.pdf.service import PDFService
from app.modules.trips.models import Trip
from app.modules.trips.repository import TripRepository
from app.modules.users.enums import UserRole
from app.modules.users.models import User


@pytest.fixture
def mock_trip_repository() -> AsyncMock:
    return AsyncMock(spec=TripRepository)


@pytest.fixture
def pdf_service(
    mock_trip_repository: AsyncMock
) -> PDFService:
    return PDFService(trip_repository=mock_trip_repository)


@pytest.fixture
def sample_user() -> User:
    user = User()
    user.id = uuid.uuid4()
    user.role = UserRole.USER
    return user


@pytest.fixture
def sample_trip(sample_user: User) -> Trip:
    trip = Trip()
    trip.id = uuid.uuid4()
    trip.user_id = sample_user.id
    trip.name = "Paris Trip"
    trip.is_deleted = False
    return trip


class TestPDFService:
    @pytest.mark.asyncio
    @patch("app.modules.pdf.service.generate_itinerary_pdf")
    async def test_trigger_itinerary_pdf_success(
        self,
        mock_generate_task: MagicMock,
        pdf_service: PDFService,
        mock_trip_repository: AsyncMock,
        sample_user: User,
        sample_trip: Trip,
    ) -> None:
        mock_trip_repository.get_by_id.return_value = sample_trip
        
        # Mock Celery delay returning a mock task object
        mock_task = MagicMock()
        mock_task.id = "mock-task-id-1234"
        mock_generate_task.delay.return_value = mock_task

        result = await pdf_service.trigger_itinerary_pdf(sample_trip.id, sample_user)
        
        assert result.task_id == "mock-task-id-1234"
        assert result.message == "PDF generation task queued successfully."
        mock_generate_task.delay.assert_called_once_with(str(sample_trip.id))

    @pytest.mark.asyncio
    @patch("app.modules.pdf.service.AsyncResult")
    async def test_get_task_status_success(
        self,
        mock_async_result: MagicMock,
        pdf_service: PDFService,
    ) -> None:
        # Mock Celery AsyncResult
        mock_result = MagicMock()
        mock_result.state = "SUCCESS"
        mock_result.result = {"file_path": "/tmp/test.pdf"}
        mock_async_result.return_value = mock_result

        result = await pdf_service.get_task_status("mock-task-id")
        
        assert result.status == "SUCCESS"
        assert result.result["file_path"] == "/tmp/test.pdf"
        mock_async_result.assert_called_once()
