"""
tests/unit/bookings/test_booking_service.py

Unit tests for BookingService.
"""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

import app.db.model_registry  # noqa: F401
from app.core.exceptions import ResourceNotFoundException
from app.modules.bookings.repository import BookingRepository
from app.modules.bookings.schemas import (
    BookingCreateRequest,
    BookingUpdateRequest,
)
from app.modules.bookings.service import BookingService
from app.modules.trips.enums import BookingStatus, BookingType
from app.modules.trips.models import Booking, Trip
from app.modules.trips.repository import TripRepository
from app.modules.users.models import User


@pytest.fixture
def mock_booking_repository() -> AsyncMock:
    return AsyncMock(spec=BookingRepository)


@pytest.fixture
def mock_trip_repository() -> AsyncMock:
    return AsyncMock(spec=TripRepository)


@pytest.fixture
def booking_service(
    mock_booking_repository: AsyncMock, mock_trip_repository: AsyncMock
) -> BookingService:
    return BookingService(
        repository=mock_booking_repository, trip_repository=mock_trip_repository
    )


@pytest.fixture
def sample_user() -> User:
    user = User()
    user.id = uuid.uuid4()
    return user


@pytest.fixture
def sample_trip(sample_user: User) -> Trip:
    trip = Trip()
    trip.id = uuid.uuid4()
    trip.user_id = sample_user.id
    return trip


@pytest.fixture
def sample_booking(sample_trip: Trip) -> Booking:
    booking = Booking()
    booking.id = uuid.uuid4()
    booking.trip_id = sample_trip.id
    booking.booking_type = BookingType.FLIGHT
    booking.provider = "Emirates"
    booking.cost = Decimal("500.00")
    booking.status = BookingStatus.CONFIRMED
    booking.is_deleted = False
    return booking


class TestBookingServiceCreate:
    @pytest.mark.asyncio
    async def test_create_booking_success(
        self,
        booking_service: BookingService,
        mock_trip_repository: AsyncMock,
        mock_booking_repository: AsyncMock,
        sample_user: User,
        sample_trip: Trip,
        sample_booking: Booking,
    ) -> None:
        mock_trip_repository.get_user_trip.return_value = sample_trip
        mock_booking_repository.create.return_value = sample_booking

        payload = BookingCreateRequest(
            booking_type=BookingType.FLIGHT,
            provider="Emirates",
            cost=Decimal("500.00"),
        )

        result = await booking_service.create_booking(sample_trip.id, payload, sample_user)
        assert result.provider == "Emirates"
        assert result.cost == Decimal("500.00")
        mock_booking_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_booking_unauthorized_trip(
        self,
        booking_service: BookingService,
        mock_trip_repository: AsyncMock,
        sample_user: User,
        sample_trip: Trip,
    ) -> None:
        mock_trip_repository.get_user_trip.return_value = None

        payload = BookingCreateRequest(booking_type=BookingType.HOTEL)

        with pytest.raises(ResourceNotFoundException):
            await booking_service.create_booking(sample_trip.id, payload, sample_user)


class TestBookingServiceGet:
    @pytest.mark.asyncio
    async def test_get_trip_bookings_success(
        self,
        booking_service: BookingService,
        mock_trip_repository: AsyncMock,
        mock_booking_repository: AsyncMock,
        sample_user: User,
        sample_trip: Trip,
        sample_booking: Booking,
    ) -> None:
        mock_trip_repository.get_user_trip.return_value = sample_trip
        mock_booking_repository.get_trip_bookings.return_value = ([sample_booking], 1)

        result = await booking_service.get_trip_bookings(sample_trip.id, sample_user)
        assert result.total == 1
        assert result.items[0].provider == "Emirates"
        mock_booking_repository.get_trip_bookings.assert_called_once()


class TestBookingServiceUpdate:
    @pytest.mark.asyncio
    async def test_update_booking_success(
        self,
        booking_service: BookingService,
        mock_trip_repository: AsyncMock,
        mock_booking_repository: AsyncMock,
        sample_user: User,
        sample_trip: Trip,
        sample_booking: Booking,
    ) -> None:
        mock_trip_repository.get_user_trip.return_value = sample_trip
        mock_booking_repository.get_by_id_and_trip.return_value = sample_booking
        mock_booking_repository.update.return_value = sample_booking

        payload = BookingUpdateRequest(provider="Qatar Airways")
        result = await booking_service.update_booking(
            sample_trip.id, sample_booking.id, payload, sample_user
        )

        assert sample_booking.provider == "Qatar Airways"
        assert result.provider == "Qatar Airways"
        mock_booking_repository.update.assert_called_once()


class TestBookingServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_booking_success(
        self,
        booking_service: BookingService,
        mock_trip_repository: AsyncMock,
        mock_booking_repository: AsyncMock,
        sample_user: User,
        sample_trip: Trip,
        sample_booking: Booking,
    ) -> None:
        mock_trip_repository.get_user_trip.return_value = sample_trip
        mock_booking_repository.get_by_id_and_trip.return_value = sample_booking

        await booking_service.delete_booking(
            sample_trip.id, sample_booking.id, sample_user
        )

        assert sample_booking.is_deleted is True
        mock_booking_repository.update.assert_called_once()
