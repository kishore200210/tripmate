"""
app/modules/itineraries/service.py

Itinerary Service — business logic for itinerary management.
"""

import logging
import uuid
from uuid import UUID

from app.core.exceptions import ResourceNotFoundException
from app.modules.itineraries.repository import ItineraryRepository
from app.modules.itineraries.schemas import (
    ItineraryItemCreateRequest,
    ItineraryItemResponse,
    ItineraryItemUpdateRequest,
    TimelineResponse,
)
from app.modules.trips.models import ItineraryItem
from app.modules.trips.repository import TripRepository
from app.modules.users.models import User
from app.shared.service import BaseService

logger = logging.getLogger(__name__)


class ItineraryService(BaseService[ItineraryRepository]):
    """Service layer for itinerary operations."""

    def __init__(
        self, repository: ItineraryRepository, trip_repository: TripRepository
    ) -> None:
        super().__init__(repository=repository)
        self.trip_repository = trip_repository

    async def _verify_trip_ownership(self, trip_id: UUID, user_id: UUID) -> None:
        """Helper to ensure a trip exists and is owned by the user."""
        trip = await self.trip_repository.get_user_trip(trip_id=trip_id, user_id=user_id)
        if not trip:
            raise ResourceNotFoundException("Trip not found.")

    async def get_timeline(self, trip_id: UUID, current_user: User) -> TimelineResponse:
        """Fetch the full itinerary timeline for a trip, ensuring ownership."""
        await self._verify_trip_ownership(trip_id, current_user.id)
        
        items = await self.repository.get_trip_timeline(trip_id)
        response_items = [ItineraryItemResponse.model_validate(item) for item in items]
        
        return TimelineResponse(
            trip_id=trip_id,
            items=response_items,
            total_items=len(response_items)
        )

    async def add_item(
        self, trip_id: UUID, payload: ItineraryItemCreateRequest, current_user: User
    ) -> ItineraryItemResponse:
        """Add an itinerary item to a trip."""
        logger.info("ItineraryService.add_item: trip_id=%s day=%s", trip_id, payload.day_no)
        await self._verify_trip_ownership(trip_id, current_user.id)

        item = ItineraryItem(
            id=uuid.uuid4(),
            trip_id=trip_id,
            day_no=payload.day_no,
            activity=payload.activity.strip(),
            scheduled_time=payload.scheduled_time,
            notes=payload.notes.strip() if payload.notes else None,
            location=payload.location.strip() if payload.location else None,
        )

        created = await self.repository.create(item)
        return ItineraryItemResponse.model_validate(created)

    async def update_item(
        self, trip_id: UUID, item_id: UUID, payload: ItineraryItemUpdateRequest, current_user: User
    ) -> ItineraryItemResponse:
        """Update or reorder an itinerary item."""
        logger.info("ItineraryService.update_item: item_id=%s", item_id)
        await self._verify_trip_ownership(trip_id, current_user.id)

        item = await self.repository.get_by_id_and_trip(item_id=item_id, trip_id=trip_id)
        if not item:
            raise ResourceNotFoundException("Itinerary item not found in this trip.")

        if payload.day_no is not None:
            item.day_no = payload.day_no
        if payload.activity is not None:
            item.activity = payload.activity.strip()
        if payload.scheduled_time is not None:
            item.scheduled_time = payload.scheduled_time
        if payload.notes is not None:
            item.notes = payload.notes.strip()
        if payload.location is not None:
            item.location = payload.location.strip()

        updated = await self.repository.update(item)
        return ItineraryItemResponse.model_validate(updated)

    async def delete_item(self, trip_id: UUID, item_id: UUID, current_user: User) -> None:
        """Soft-delete an itinerary item."""
        logger.info("ItineraryService.delete_item: item_id=%s", item_id)
        await self._verify_trip_ownership(trip_id, current_user.id)

        item = await self.repository.get_by_id_and_trip(item_id=item_id, trip_id=trip_id)
        if not item:
            raise ResourceNotFoundException("Itinerary item not found in this trip.")

        item.soft_delete()
        await self.repository.update(item)
