"""
app/modules/trips/controller.py

Trip Controller — thin HTTP translation layer for trips.
"""

from uuid import UUID

from app.modules.auth.schemas import MessageResponse
from app.modules.trips.enums import TripStatus
from app.modules.trips.schemas import (
    TripCreateRequest,
    TripPaginatedResponse,
    TripResponse,
    TripUpdateRequest,
)
from app.modules.trips.service import TripService
from app.modules.users.models import User


class TripController:
    """Thin HTTP controller for the Trips module."""

    @staticmethod
    async def get_user_trips(
        skip: int,
        limit: int,
        status: TripStatus | None,
        query: str | None,
        service: TripService,
        current_user: User,
    ) -> TripPaginatedResponse:
        return await service.get_user_trips(
            current_user, skip=skip, limit=limit, status=status, query=query
        )

    @staticmethod
    async def get_trip(
        trip_id: UUID, service: TripService, current_user: User
    ) -> TripResponse:
        return await service.get_trip(trip_id, current_user)

    @staticmethod
    async def create_trip(
        payload: TripCreateRequest, service: TripService, current_user: User
    ) -> TripResponse:
        return await service.create_trip(payload, current_user)

    @staticmethod
    async def update_trip(
        trip_id: UUID, payload: TripUpdateRequest, service: TripService, current_user: User
    ) -> TripResponse:
        return await service.update_trip(trip_id, payload, current_user)

    @staticmethod
    async def delete_trip(
        trip_id: UUID, service: TripService, current_user: User
    ) -> MessageResponse:
        await service.delete_trip(trip_id, current_user)
        return MessageResponse(message="Trip deleted successfully.")
