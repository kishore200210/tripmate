"""
app/modules/bookings/service.py

Booking Service — business logic for booking management.
"""

import logging
import uuid
from uuid import UUID

from app.core.exceptions import ResourceNotFoundException
from app.modules.bookings.repository import BookingRepository
from app.modules.bookings.schemas import (
    BookingCreateRequest,
    BookingPaginatedResponse,
    BookingResponse,
    BookingUpdateRequest,
)
from app.modules.trips.enums import BookingType
from app.modules.trips.models import Booking
from app.modules.trips.repository import TripRepository
from app.modules.users.models import User
from app.shared.service import BaseService

logger = logging.getLogger(__name__)


class BookingService(BaseService[BookingRepository]):
    """Service layer for booking operations."""

    def __init__(
        self, repository: BookingRepository, trip_repository: TripRepository
    ) -> None:
        super().__init__(repository=repository)
        self.trip_repository = trip_repository

    async def _verify_trip_ownership(self, trip_id: UUID, user_id: UUID) -> None:
        """Helper to ensure a trip exists and is owned by the user."""
        trip = await self.trip_repository.get_user_trip(trip_id=trip_id, user_id=user_id)
        if not trip:
            raise ResourceNotFoundException("Trip not found.")

    async def get_trip_bookings(
        self, trip_id: UUID, current_user: User, skip: int = 0, limit: int = 20, booking_type: BookingType | None = None
    ) -> BookingPaginatedResponse:
        """Fetch all bookings for a trip, ensuring ownership."""
        await self._verify_trip_ownership(trip_id, current_user.id)
        
        items, total = await self.repository.get_trip_bookings(
            trip_id=trip_id, skip=skip, limit=limit, booking_type=booking_type
        )
        
        return BookingPaginatedResponse(
            items=[BookingResponse.model_validate(item) for item in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_booking(self, trip_id: UUID, booking_id: UUID, current_user: User) -> BookingResponse:
        """Fetch a specific booking ensuring ownership."""
        await self._verify_trip_ownership(trip_id, current_user.id)
        
        booking = await self.repository.get_by_id_and_trip(booking_id=booking_id, trip_id=trip_id)
        if not booking:
            raise ResourceNotFoundException("Booking not found in this trip.")
            
        return BookingResponse.model_validate(booking)

    async def create_booking(
        self, trip_id: UUID, payload: BookingCreateRequest, current_user: User
    ) -> BookingResponse:
        """Create a new booking for a trip."""
        logger.info("BookingService.create_booking: trip_id=%s type=%s", trip_id, payload.booking_type)
        await self._verify_trip_ownership(trip_id, current_user.id)

        booking = Booking(
            id=uuid.uuid4(),
            trip_id=trip_id,
            booking_type=payload.booking_type,
            provider=payload.provider.strip() if payload.provider else None,
            cost=payload.cost,
            status=payload.status,
            confirmation_ref=payload.confirmation_ref.strip() if payload.confirmation_ref else None,
            notes=payload.notes.strip() if payload.notes else None,
            booked_at=payload.booked_at,
        )

        created = await self.repository.create(booking)
        return BookingResponse.model_validate(created)

    async def update_booking(
        self, trip_id: UUID, booking_id: UUID, payload: BookingUpdateRequest, current_user: User
    ) -> BookingResponse:
        """Update an existing booking."""
        logger.info("BookingService.update_booking: booking_id=%s", booking_id)
        await self._verify_trip_ownership(trip_id, current_user.id)

        booking = await self.repository.get_by_id_and_trip(booking_id=booking_id, trip_id=trip_id)
        if not booking:
            raise ResourceNotFoundException("Booking not found in this trip.")

        if payload.booking_type is not None:
            booking.booking_type = payload.booking_type
        if payload.provider is not None:
            booking.provider = payload.provider.strip()
        if payload.cost is not None:
            booking.cost = payload.cost
        if payload.status is not None:
            booking.status = payload.status
        if payload.confirmation_ref is not None:
            booking.confirmation_ref = payload.confirmation_ref.strip()
        if payload.notes is not None:
            booking.notes = payload.notes.strip()
        if payload.booked_at is not None:
            booking.booked_at = payload.booked_at

        updated = await self.repository.update(booking)
        return BookingResponse.model_validate(updated)

    async def delete_booking(self, trip_id: UUID, booking_id: UUID, current_user: User) -> None:
        """Soft-delete a booking."""
        logger.info("BookingService.delete_booking: booking_id=%s", booking_id)
        await self._verify_trip_ownership(trip_id, current_user.id)

        booking = await self.repository.get_by_id_and_trip(booking_id=booking_id, trip_id=trip_id)
        if not booking:
            raise ResourceNotFoundException("Booking not found in this trip.")

        booking.soft_delete()
        await self.repository.update(booking)
