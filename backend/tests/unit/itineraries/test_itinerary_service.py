"""
tests/unit/itineraries/test_itinerary_service.py

Unit tests for ItineraryService.
"""

import uuid
from datetime import time
from unittest.mock import AsyncMock, patch

import pytest

import app.db.model_registry  # noqa: F401
from app.core.exceptions import ResourceNotFoundException
from app.modules.itineraries.repository import ItineraryRepository
from app.modules.itineraries.schemas import (
    ItineraryItemCreateRequest,
    ItineraryItemUpdateRequest,
    ItineraryResponse,
    AIGenerateRequest,
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


from app.core.exceptions import ResourceNotFoundException, ValidationException

class TestItineraryServiceGenerate:
    @pytest.mark.asyncio
    @patch("app.modules.itineraries.service.ItineraryGenerator")
    async def test_generate_full_itinerary_success(
        self,
        mock_generator_class,
        itinerary_service: ItineraryService,
        mock_trip_repository: AsyncMock,
        mock_itinerary_repository: AsyncMock,
        sample_user: User,
        sample_trip: Trip,
    ) -> None:
        mock_trip_repository.get_user_trip.return_value = sample_trip
        mock_generator_instance = mock_generator_class.return_value
        mock_generator_instance.generate_itinerary = AsyncMock(return_value={
            "budget_estimate": "1000",
            "packing_checklist": ["Item 1"],
            "restaurant_recommendations": ["Rest 1"],
            "local_attractions": ["Attr 1"],
            "weather_suggestions": "Sunny",
            "day_plans": [
                {
                    "day_no": 1,
                    "theme": "Arrival",
                    "description": "Arrive and rest",
                    "activities": [
                        {
                            "activity": "Check-in",
                            "scheduled_time": "14:00:00",
                            "notes": "",
                            "location": "Hotel"
                        }
                    ]
                }
            ]
        })
        
        mock_itinerary_repository.db = AsyncMock()
        
        mock_itinerary = ItineraryResponse(
            id=uuid.uuid4(),
            trip_id=sample_trip.id,
            budget_estimate="1000",
            packing_checklist='["Item 1"]',
            restaurant_recommendations='["Rest 1"]',
            local_attractions='["Attr 1"]',
            weather_suggestions="Sunny",
            day_plans=[]
        )
        with patch.object(itinerary_service, "get_ai_itinerary", return_value=mock_itinerary):
            payload = AIGenerateRequest(preferences="Relaxing")
            result = await itinerary_service.generate_full_itinerary(sample_trip.id, payload, sample_user)
            
            assert result.budget_estimate == "1000"
            mock_generator_instance.generate_itinerary.assert_called_once()
            mock_itinerary_repository.db.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.modules.itineraries.service.ItineraryGenerator")
    async def test_regenerate_day_plan_success_day_1(
        self,
        mock_generator_class,
        itinerary_service: ItineraryService,
        mock_trip_repository: AsyncMock,
        mock_itinerary_repository: AsyncMock,
        sample_user: User,
        sample_trip: Trip,
    ) -> None:
        mock_trip_repository.get_user_trip.return_value = sample_trip
        mock_generator_instance = mock_generator_class.return_value
        mock_generator_instance.regenerate_day = AsyncMock(return_value={
            "theme": "Day 1 New Theme",
            "description": "Day 1 New Desc",
            "activities": []
        })
        
        mock_itinerary_repository.db = AsyncMock()
        
        from app.modules.trips.models import Itinerary, DayPlan
        mock_itinerary_db = Itinerary(id=uuid.uuid4(), trip_id=sample_trip.id, budget_estimate="500")
        mock_day_plan_db = DayPlan(id=uuid.uuid4(), itinerary_id=mock_itinerary_db.id, day_no=1, theme="Old Day 1", description="Old Desc")
        
        async def mock_scalar_side_effect(stmt):
            stmt_str = str(stmt).lower()
            if "day_plans" in stmt_str:
                return mock_day_plan_db
            elif "itineraries" in stmt_str:
                return mock_itinerary_db
            return None
            
        mock_itinerary_repository.db.scalar.side_effect = mock_scalar_side_effect
        
        mock_itinerary_resp = ItineraryResponse(
            id=mock_itinerary_db.id,
            trip_id=sample_trip.id,
            budget_estimate="500",
            packing_checklist=None,
            restaurant_recommendations=None,
            local_attractions=None,
            weather_suggestions=None,
            day_plans=[]
        )
        with patch.object(itinerary_service, "get_ai_itinerary", return_value=mock_itinerary_resp):
            payload = AIGenerateRequest(preferences="Fun")
            result = await itinerary_service.regenerate_day_plan(sample_trip.id, 1, payload, sample_user)
            
            assert result.id == mock_itinerary_db.id
            assert mock_day_plan_db.day_no == 1
            assert mock_day_plan_db.theme == "Day 1 New Theme"
            mock_generator_instance.regenerate_day.assert_called_once_with(sample_trip.title, 1, "Old Day 1", "Fun")
            mock_itinerary_repository.db.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.modules.itineraries.service.ItineraryGenerator")
    async def test_regenerate_day_plan_success_day_5(
        self,
        mock_generator_class,
        itinerary_service: ItineraryService,
        mock_trip_repository: AsyncMock,
        mock_itinerary_repository: AsyncMock,
        sample_user: User,
        sample_trip: Trip,
    ) -> None:
        mock_trip_repository.get_user_trip.return_value = sample_trip
        mock_generator_instance = mock_generator_class.return_value
        mock_generator_instance.regenerate_day = AsyncMock(return_value={
            "theme": "Day 5 Adventure",
            "description": "Day 5 Desc",
            "activities": []
        })
        
        mock_itinerary_repository.db = AsyncMock()
        
        from app.modules.trips.models import Itinerary, DayPlan
        mock_itinerary_db = Itinerary(id=uuid.uuid4(), trip_id=sample_trip.id)
        mock_day_plan_db = DayPlan(id=uuid.uuid4(), itinerary_id=mock_itinerary_db.id, day_no=5, theme="Old Day 5", description="Old")
        
        async def mock_scalar_side_effect(stmt):
            stmt_str = str(stmt).lower()
            if "day_plans" in stmt_str:
                return mock_day_plan_db
            elif "itineraries" in stmt_str:
                return mock_itinerary_db
            return None
            
        mock_itinerary_repository.db.scalar.side_effect = mock_scalar_side_effect
        
        mock_itinerary_resp = ItineraryResponse(
            id=mock_itinerary_db.id,
            trip_id=sample_trip.id,
            budget_estimate="1000",
            packing_checklist=None,
            restaurant_recommendations=None,
            local_attractions=None,
            weather_suggestions=None,
            day_plans=[]
        )
        with patch.object(itinerary_service, "get_ai_itinerary", return_value=mock_itinerary_resp):
            payload = AIGenerateRequest(preferences="Hiking")
            result = await itinerary_service.regenerate_day_plan(sample_trip.id, 5, payload, sample_user)
            
            assert mock_day_plan_db.day_no == 5
            assert mock_day_plan_db.theme == "Day 5 Adventure"
            mock_generator_instance.regenerate_day.assert_called_once_with(sample_trip.title, 5, "Old Day 5", "Hiking")

    @pytest.mark.asyncio
    async def test_regenerate_day_plan_invalid_day_0_raises_exception(
        self,
        itinerary_service: ItineraryService,
        sample_user: User,
        sample_trip: Trip,
    ) -> None:
        payload = AIGenerateRequest(preferences="Relaxing")
        with pytest.raises(ValidationException) as exc_info:
            await itinerary_service.regenerate_day_plan(sample_trip.id, 0, payload, sample_user)
        assert "Day number must be greater than 0" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_regenerate_day_plan_negative_day_raises_exception(
        self,
        itinerary_service: ItineraryService,
        sample_user: User,
        sample_trip: Trip,
    ) -> None:
        payload = AIGenerateRequest(preferences="Relaxing")
        with pytest.raises(ValidationException) as exc_info:
            await itinerary_service.regenerate_day_plan(sample_trip.id, -1, payload, sample_user)
        assert "Day number must be greater than 0" in str(exc_info.value)

