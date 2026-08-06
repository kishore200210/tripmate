"""
tests/unit/itineraries/test_itinerary_service.py

Unit tests for ItineraryService.
"""

import uuid
from datetime import time
from unittest.mock import AsyncMock

import pytest

import app.db.model_registry  # noqa: F401
from app.core.exceptions import ResourceNotFoundException
from app.modules.itineraries.repository import ItineraryRepository
from app.modules.itineraries.schemas import (
    ItineraryItemCreateRequest,
    ItineraryItemUpdateRequest,
)
from app.modules.itineraries.service import ItineraryService
from app.modules.trips.models import ItineraryItem, Trip
from app.modules.trips.repository import TripRepository
from app.modules.users.models import User


@pytest.fixture
def mock_itinerary_repository() -> AsyncMock:
    return AsyncMock(spec=ItineraryRepository)


@pytest.fixture
def mock_trip_repository() -> AsyncMock:
    return AsyncMock(spec=TripRepository)


@pytest.fixture
def itinerary_service(
    mock_itinerary_repository: AsyncMock, mock_trip_repository: AsyncMock
) -> ItineraryService:
    return ItineraryService(
        repository=mock_itinerary_repository, trip_repository=mock_trip_repository
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
def sample_itinerary_item(sample_trip: Trip) -> ItineraryItem:
    item = ItineraryItem()
    item.id = uuid.uuid4()
    item.trip_id = sample_trip.id
    item.day_no = 1
    item.activity = "Visit Eiffel Tower"
    item.scheduled_time = time(9, 0)
    item.is_deleted = False
    return item


class TestItineraryServiceCreate:
    @pytest.mark.asyncio
    async def test_add_item_success(
        self,
        itinerary_service: ItineraryService,
        mock_trip_repository: AsyncMock,
        mock_itinerary_repository: AsyncMock,
        sample_user: User,
        sample_trip: Trip,
        sample_itinerary_item: ItineraryItem,
    ) -> None:
        mock_trip_repository.get_user_trip.return_value = sample_trip
        mock_itinerary_repository.create.return_value = sample_itinerary_item

        payload = ItineraryItemCreateRequest(
            day_no=1, activity="Visit Eiffel Tower", scheduled_time=time(9, 0)
        )

        result = await itinerary_service.add_item(sample_trip.id, payload, sample_user)
        assert result.activity == "Visit Eiffel Tower"
        mock_itinerary_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_item_unauthorized_trip(
        self,
        itinerary_service: ItineraryService,
        mock_trip_repository: AsyncMock,
        sample_user: User,
        sample_trip: Trip,
    ) -> None:
        mock_trip_repository.get_user_trip.return_value = None

        payload = ItineraryItemCreateRequest(day_no=1, activity="Unauthorized")

        with pytest.raises(ResourceNotFoundException):
            await itinerary_service.add_item(sample_trip.id, payload, sample_user)


class TestItineraryServiceGet:
    @pytest.mark.asyncio
    async def test_get_timeline_success(
        self,
        itinerary_service: ItineraryService,
        mock_trip_repository: AsyncMock,
        mock_itinerary_repository: AsyncMock,
        sample_user: User,
        sample_trip: Trip,
        sample_itinerary_item: ItineraryItem,
    ) -> None:
        mock_trip_repository.get_user_trip.return_value = sample_trip
        mock_itinerary_repository.get_trip_timeline.return_value = [sample_itinerary_item]

        result = await itinerary_service.get_timeline(sample_trip.id, sample_user)
        assert result.total_items == 1
        assert result.items[0].activity == "Visit Eiffel Tower"
        mock_itinerary_repository.get_trip_timeline.assert_called_once()


class TestItineraryServiceUpdate:
    @pytest.mark.asyncio
    async def test_update_item_success(
        self,
        itinerary_service: ItineraryService,
        mock_trip_repository: AsyncMock,
        mock_itinerary_repository: AsyncMock,
        sample_user: User,
        sample_trip: Trip,
        sample_itinerary_item: ItineraryItem,
    ) -> None:
        mock_trip_repository.get_user_trip.return_value = sample_trip
        mock_itinerary_repository.get_by_id_and_trip.return_value = sample_itinerary_item
        mock_itinerary_repository.update.return_value = sample_itinerary_item

        payload = ItineraryItemUpdateRequest(activity="Visit Louvre", day_no=2)
        result = await itinerary_service.update_item(
            sample_trip.id, sample_itinerary_item.id, payload, sample_user
        )

        assert sample_itinerary_item.activity == "Visit Louvre"
        assert sample_itinerary_item.day_no == 2
        assert result.activity == "Visit Louvre"
        mock_itinerary_repository.update.assert_called_once()


class TestItineraryServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_item_success(
        self,
        itinerary_service: ItineraryService,
        mock_trip_repository: AsyncMock,
        mock_itinerary_repository: AsyncMock,
        sample_user: User,
        sample_trip: Trip,
        sample_itinerary_item: ItineraryItem,
    ) -> None:
        mock_trip_repository.get_user_trip.return_value = sample_trip
        mock_itinerary_repository.get_by_id_and_trip.return_value = sample_itinerary_item

        await itinerary_service.delete_item(
            sample_trip.id, sample_itinerary_item.id, sample_user
        )

        assert sample_itinerary_item.is_deleted is True
        mock_itinerary_repository.update.assert_called_once()
