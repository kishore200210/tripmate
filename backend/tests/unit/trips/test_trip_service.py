"""
tests/unit/trips/test_trip_service.py

Unit tests for TripService.
"""

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

import app.db.model_registry  # noqa: F401
from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.modules.destinations.models import Destination
from app.modules.destinations.repository import DestinationRepository
from app.modules.trips.enums import TripStatus
from app.modules.trips.models import Trip
from app.modules.trips.repository import TripRepository
from app.modules.trips.schemas import TripCreateRequest, TripUpdateRequest
from app.modules.trips.service import TripService
from app.modules.users.models import User


@pytest.fixture
def mock_trip_repository() -> AsyncMock:
    return AsyncMock(spec=TripRepository)


@pytest.fixture
def mock_dest_repository() -> AsyncMock:
    return AsyncMock(spec=DestinationRepository)


@pytest.fixture
def trip_service(mock_trip_repository: AsyncMock, mock_dest_repository: AsyncMock) -> TripService:
    return TripService(repository=mock_trip_repository, destination_repository=mock_dest_repository)


@pytest.fixture
def sample_user() -> User:
    user = User()
    user.id = uuid.uuid4()
    return user


@pytest.fixture
def sample_destination() -> Destination:
    dest = Destination()
    dest.id = uuid.uuid4()
    dest.is_deleted = False
    dest.is_active = True
    return dest


@pytest.fixture
def sample_trip(sample_user: User) -> Trip:
    trip = Trip()
    trip.id = uuid.uuid4()
    trip.title = "Summer Vacation"
    trip.description = "Fun in the sun"
    trip.start_date = date.today()
    trip.end_date = date.today() + timedelta(days=5)
    trip.budget = Decimal("1000.00")
    trip.status = TripStatus.PLANNING
    trip.user_id = sample_user.id
    trip.destination_id = None
    trip.place_name = None
    trip.place_country = None
    trip.cover_image_url = None
    trip.is_deleted = False
    trip.created_at = datetime.now(tz=timezone.utc)
    trip.updated_at = datetime.now(tz=timezone.utc)
    return trip


class TestTripServiceCreate:
    @pytest.mark.asyncio
    async def test_create_trip_success(
        self, trip_service: TripService, mock_trip_repository: AsyncMock, sample_user: User, sample_trip: Trip
    ) -> None:
        mock_trip_repository.create.return_value = sample_trip

        payload = TripCreateRequest(
            title="Summer Vacation",
            budget=Decimal("1000.00"),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=5)
        )

        result = await trip_service.create_trip(payload, sample_user)
        assert result.title == "Summer Vacation"
        mock_trip_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_trip_invalid_destination(
        self, trip_service: TripService, mock_dest_repository: AsyncMock, sample_user: User
    ) -> None:
        mock_dest_repository.get_by_id.return_value = None

        payload = TripCreateRequest(
            title="Summer Vacation",
            destination_id=uuid.uuid4()
        )

        with pytest.raises(ValidationException, match="Invalid or inactive destination selected"):
            await trip_service.create_trip(payload, sample_user)


class TestTripServiceGet:
    @pytest.mark.asyncio
    async def test_get_user_trips(
        self, trip_service: TripService, mock_trip_repository: AsyncMock, sample_user: User, sample_trip: Trip
    ) -> None:
        mock_trip_repository.get_user_trips.return_value = ([sample_trip], 1)

        result = await trip_service.get_user_trips(sample_user)
        assert result.total == 1
        assert result.items[0].title == "Summer Vacation"
        mock_trip_repository.get_user_trips.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_trip_not_found_or_not_owned(
        self, trip_service: TripService, mock_trip_repository: AsyncMock, sample_user: User
    ) -> None:
        mock_trip_repository.get_user_trip.return_value = None

        with pytest.raises(ResourceNotFoundException):
            await trip_service.get_trip(uuid.uuid4(), sample_user)


class TestTripServiceUpdate:
    @pytest.mark.asyncio
    async def test_update_trip_success(
        self, trip_service: TripService, mock_trip_repository: AsyncMock, sample_user: User, sample_trip: Trip
    ) -> None:
        mock_trip_repository.get_user_trip.return_value = sample_trip
        mock_trip_repository.update.return_value = sample_trip

        payload = TripUpdateRequest(title="Winter Vacation")
        result = await trip_service.update_trip(sample_trip.id, payload, sample_user)
        
        assert sample_trip.title == "Winter Vacation"
        assert result.title == "Winter Vacation"
        mock_trip_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_trip_invalid_dates_raises_exception(
        self, trip_service: TripService, mock_trip_repository: AsyncMock, sample_user: User, sample_trip: Trip
    ) -> None:
        mock_trip_repository.get_user_trip.return_value = sample_trip

        # start_date becomes strictly greater than the existing end_date
        payload = TripUpdateRequest(start_date=sample_trip.end_date + timedelta(days=1))
        
        with pytest.raises(ValidationException, match="start_date cannot be after end_date"):
            await trip_service.update_trip(sample_trip.id, payload, sample_user)


class TestTripServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_trip_success(
        self, trip_service: TripService, mock_trip_repository: AsyncMock, sample_user: User, sample_trip: Trip
    ) -> None:
        mock_trip_repository.get_user_trip.return_value = sample_trip

        await trip_service.delete_trip(sample_trip.id, sample_user)
        assert sample_trip.is_deleted is True
        mock_trip_repository.update.assert_called_once()
