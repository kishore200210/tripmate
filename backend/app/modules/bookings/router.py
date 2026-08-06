"""
app/modules/bookings/router.py

Bookings API Router — URL mapping and Swagger documentation.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.middleware import get_current_user
from app.modules.auth.schemas import MessageResponse
from app.modules.bookings.controller import BookingController
from app.modules.bookings.repository import BookingRepository
from app.modules.bookings.schemas import (
    BookingCreateRequest,
    BookingPaginatedResponse,
    BookingResponse,
    BookingUpdateRequest,
)
from app.modules.bookings.service import BookingService
from app.modules.trips.enums import BookingType
from app.modules.trips.repository import TripRepository
from app.modules.users.models import User

router = APIRouter(
    prefix="/trips/{trip_id}/bookings",
    tags=["Bookings"],
)


# ── Dependency Factory ────────────────────────────────────────────────────────

def get_booking_service(db: AsyncSession = Depends(get_db)) -> BookingService:
    repository = BookingRepository(db=db)
    trip_repository = TripRepository(db=db)
    return BookingService(repository=repository, trip_repository=trip_repository)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=BookingPaginatedResponse,
    summary="List all bookings for a trip",
)
async def list_trip_bookings(
    trip_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    booking_type: BookingType | None = Query(None, description="Filter by booking type"),
    current_user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> BookingPaginatedResponse:
    return await BookingController.get_trip_bookings(
        trip_id, skip=skip, limit=limit, booking_type=booking_type, service=service, current_user=current_user
    )


@router.get(
    "/{booking_id}",
    response_model=BookingResponse,
    summary="Get a specific booking by ID",
)
async def get_booking(
    trip_id: UUID,
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> BookingResponse:
    return await BookingController.get_booking(trip_id, booking_id, service, current_user)


@router.post(
    "/",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new booking",
)
async def create_booking(
    trip_id: UUID,
    payload: BookingCreateRequest,
    current_user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> BookingResponse:
    return await BookingController.create_booking(trip_id, payload, service, current_user)


@router.patch(
    "/{booking_id}",
    response_model=BookingResponse,
    summary="Update a booking",
)
async def update_booking(
    trip_id: UUID,
    booking_id: UUID,
    payload: BookingUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> BookingResponse:
    return await BookingController.update_booking(trip_id, booking_id, payload, service, current_user)


@router.delete(
    "/{booking_id}",
    response_model=MessageResponse,
    summary="Delete a booking",
)
async def delete_booking(
    trip_id: UUID,
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> MessageResponse:
    return await BookingController.delete_booking(trip_id, booking_id, service, current_user)
