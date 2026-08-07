"""
app/modules/trips/service.py

Trip Service — business logic for trip management.
"""

import logging
import uuid
from uuid import UUID

from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.modules.destinations.repository import DestinationRepository
from app.modules.trips.enums import TripStatus
from app.modules.trips.models import Trip
from app.modules.trips.repository import TripRepository
from app.modules.trips.schemas import (
    TripCreateRequest,
    TripPaginatedResponse,
    TripResponse,
    TripUpdateRequest,
)
from app.modules.users.models import User
from app.shared.service import BaseService

logger = logging.getLogger(__name__)


class TripService(BaseService[TripRepository]):
    """Service layer for trip operations."""

    def __init__(
        self, repository: TripRepository, destination_repository: DestinationRepository
    ) -> None:
        super().__init__(repository=repository)
        self.destination_repository = destination_repository

    async def get_user_trips(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 20,
        status: TripStatus | None = None,
        query: str | None = None,
    ) -> TripPaginatedResponse:
        """List trips belonging to the authenticated user."""
        items, total = await self.repository.get_user_trips(
            user_id=current_user.id, skip=skip, limit=limit, status=status, query=query
        )
        return TripPaginatedResponse(
            items=[TripResponse.model_validate(t) for t in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_trip(self, trip_id: UUID, current_user: User) -> TripResponse:
        """Get a specific trip, ensuring ownership."""
        trip = await self.repository.get_user_trip(trip_id=trip_id, user_id=current_user.id)
        if not trip:
            raise ResourceNotFoundException("Trip not found.")
        return TripResponse.model_validate(trip)

    async def create_trip(self, payload: TripCreateRequest, current_user: User) -> TripResponse:
        """Create a new trip for the current user."""
        logger.info("TripService.create_trip: user_id=%s", current_user.id)

        # Validate destination if provided
        if payload.destination_id:
            dest = await self.destination_repository.get_by_id(payload.destination_id)
            if not dest or dest.is_deleted or not dest.is_active:
                raise ValidationException("Invalid or inactive destination selected.")

        trip = Trip(
            id=uuid.uuid4(),
            title=payload.title.strip(),
            description=payload.description.strip() if payload.description else None,
            start_date=payload.start_date,
            end_date=payload.end_date,
            budget=payload.budget,
            destination_id=payload.destination_id,
            place_name=payload.place_name.strip() if payload.place_name else None,
            place_country=payload.place_country.strip() if payload.place_country else None,
            user_id=current_user.id,
            status=TripStatus.PLANNING,
        )

        created = await self.repository.create(trip)
        return TripResponse.model_validate(created)

    async def update_trip(
        self, trip_id: UUID, payload: TripUpdateRequest, current_user: User
    ) -> TripResponse:
        """Update a trip, ensuring ownership."""
        logger.info("TripService.update_trip: trip_id=%s", trip_id)
        
        trip = await self.repository.get_user_trip(trip_id=trip_id, user_id=current_user.id)
        if not trip:
            raise ResourceNotFoundException("Trip not found.")

        # If partial dates are provided, we must validate against existing dates
        new_start = payload.start_date if payload.start_date is not None else trip.start_date
        new_end = payload.end_date if payload.end_date is not None else trip.end_date

        if new_start and new_end and new_start > new_end:
            raise ValidationException("start_date cannot be after end_date")

        if payload.destination_id is not None:
            dest = await self.destination_repository.get_by_id(payload.destination_id)
            if not dest or dest.is_deleted or not dest.is_active:
                raise ValidationException("Invalid or inactive destination selected.")
            trip.destination_id = payload.destination_id

        if payload.title is not None:
            trip.title = payload.title.strip()
        if payload.description is not None:
            trip.description = payload.description.strip()
        if payload.place_name is not None:
            trip.place_name = payload.place_name.strip()
        if payload.place_country is not None:
            trip.place_country = payload.place_country.strip()
        
        trip.start_date = new_start
        trip.end_date = new_end
        
        if payload.budget is not None:
            trip.budget = payload.budget
        if payload.status is not None:
            trip.status = payload.status

        updated = await self.repository.update(trip)
        return TripResponse.model_validate(updated)

    async def delete_trip(self, trip_id: UUID, current_user: User) -> None:
        """Soft-delete a trip, ensuring ownership."""
        logger.info("TripService.delete_trip: trip_id=%s", trip_id)
        trip = await self.repository.get_user_trip(trip_id=trip_id, user_id=current_user.id)
        if not trip:
            raise ResourceNotFoundException("Trip not found.")

        trip.soft_delete()
        await self.repository.update(trip)
