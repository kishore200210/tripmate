"""
app/modules/bookings/controller.py

Booking Controller — thin HTTP translation layer for bookings.
"""

from uuid import UUID

from app.modules.auth.schemas import MessageResponse
from app.modules.bookings.schemas import (
    BookingCreateRequest,
    BookingPaginatedResponse,
    BookingResponse,
    BookingUpdateRequest,
)
from app.modules.bookings.service import BookingService
from app.modules.trips.enums import BookingType
from app.modules.users.models import User


class BookingController:
    """Thin HTTP controller for the Bookings module."""

    @staticmethod
    async def get_trip_bookings(
        trip_id: UUID, skip: int, limit: int, booking_type: BookingType | None, service: BookingService, current_user: User
    ) -> BookingPaginatedResponse:
        return await service.get_trip_bookings(
            trip_id, current_user, skip=skip, limit=limit, booking_type=booking_type
        )

    @staticmethod
    async def get_booking(
        trip_id: UUID, booking_id: UUID, service: BookingService, current_user: User
    ) -> BookingResponse:
        return await service.get_booking(trip_id, booking_id, current_user)

    @staticmethod
    async def create_booking(
        trip_id: UUID, payload: BookingCreateRequest, service: BookingService, current_user: User
    ) -> BookingResponse:
        return await service.create_booking(trip_id, payload, current_user)

    @staticmethod
    async def update_booking(
        trip_id: UUID, booking_id: UUID, payload: BookingUpdateRequest, service: BookingService, current_user: User
    ) -> BookingResponse:
        return await service.update_booking(trip_id, booking_id, payload, current_user)

    @staticmethod
    async def delete_booking(
        trip_id: UUID, booking_id: UUID, service: BookingService, current_user: User
    ) -> MessageResponse:
        await service.delete_booking(trip_id, booking_id, current_user)
        return MessageResponse(message="Booking deleted successfully.")
