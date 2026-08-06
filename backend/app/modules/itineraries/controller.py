"""
app/modules/itineraries/controller.py

Itinerary Controller — thin HTTP translation layer for itineraries.
"""

from uuid import UUID

from app.modules.auth.schemas import MessageResponse
from app.modules.itineraries.schemas import (
    ItineraryItemCreateRequest,
    ItineraryItemResponse,
    ItineraryItemUpdateRequest,
    TimelineResponse,
    ItineraryResponse,
    AIGenerateRequest,
)
from app.modules.itineraries.service import ItineraryService
from app.modules.users.models import User


class ItineraryController:
    """Thin HTTP controller for the Itineraries module."""

    @staticmethod
    async def get_timeline(
        trip_id: UUID, service: ItineraryService, current_user: User
    ) -> TimelineResponse:
        return await service.get_timeline(trip_id, current_user)

    @staticmethod
    async def get_ai_itinerary(
        trip_id: UUID, service: ItineraryService, current_user: User
    ) -> ItineraryResponse | None:
        return await service.get_ai_itinerary(trip_id, current_user)

    @staticmethod
    async def generate_full_itinerary(
        trip_id: UUID, payload: AIGenerateRequest, service: ItineraryService, current_user: User
    ) -> ItineraryResponse:
        return await service.generate_full_itinerary(trip_id, payload, current_user)

    @staticmethod
    async def regenerate_day_plan(
        trip_id: UUID, day_no: int, payload: AIGenerateRequest, service: ItineraryService, current_user: User
    ) -> ItineraryResponse:
        return await service.regenerate_day_plan(trip_id, day_no, payload, current_user)

    @staticmethod
    async def add_item(
        trip_id: UUID, payload: ItineraryItemCreateRequest, service: ItineraryService, current_user: User
    ) -> ItineraryItemResponse:
        return await service.add_item(trip_id, payload, current_user)

    @staticmethod
    async def update_item(
        trip_id: UUID, item_id: UUID, payload: ItineraryItemUpdateRequest, service: ItineraryService, current_user: User
    ) -> ItineraryItemResponse:
        return await service.update_item(trip_id, item_id, payload, current_user)

    @staticmethod
    async def delete_item(
        trip_id: UUID, item_id: UUID, service: ItineraryService, current_user: User
    ) -> MessageResponse:
        await service.delete_item(trip_id, item_id, current_user)
        return MessageResponse(message="Itinerary item deleted successfully.")
