"""
app/modules/trips/router.py

Trips API Router — URL mapping and Swagger documentation.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.middleware import get_current_user
from app.modules.auth.schemas import MessageResponse
from app.modules.destinations.repository import DestinationRepository
from app.modules.trips.controller import TripController
from app.modules.trips.enums import TripStatus
from app.modules.trips.repository import TripRepository
from app.modules.trips.schemas import (
    TripCreateRequest,
    TripPaginatedResponse,
    TripResponse,
    TripUpdateRequest,
)
from app.modules.trips.service import TripService
from app.modules.users.models import User

router = APIRouter(
    prefix="/trips",
    tags=["Trips"],
)


# ── Dependency Factory ────────────────────────────────────────────────────────

def get_trip_service(db: AsyncSession = Depends(get_db)) -> TripService:
    repository = TripRepository(db=db)
    destination_repository = DestinationRepository(db=db)
    return TripService(repository=repository, destination_repository=destination_repository)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=TripPaginatedResponse,
    summary="List all trips for the current user",
)
async def list_trips(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    trip_status: TripStatus | None = Query(None, description="Filter trips by status"),
    current_user: User = Depends(get_current_user),
    service: TripService = Depends(get_trip_service),
) -> TripPaginatedResponse:
    return await TripController.get_user_trips(
        skip=skip, limit=limit, status=trip_status, service=service, current_user=current_user
    )


@router.get(
    "/{trip_id}",
    response_model=TripResponse,
    summary="Get a specific trip by ID",
)
async def get_trip(
    trip_id: UUID,
    current_user: User = Depends(get_current_user),
    service: TripService = Depends(get_trip_service),
) -> TripResponse:
    return await TripController.get_trip(trip_id, service, current_user)


@router.post(
    "/",
    response_model=TripResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new trip",
)
async def create_trip(
    payload: TripCreateRequest,
    current_user: User = Depends(get_current_user),
    service: TripService = Depends(get_trip_service),
) -> TripResponse:
    return await TripController.create_trip(payload, service, current_user)


@router.patch(
    "/{trip_id}",
    response_model=TripResponse,
    summary="Update a trip",
)
async def update_trip(
    trip_id: UUID,
    payload: TripUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: TripService = Depends(get_trip_service),
) -> TripResponse:
    return await TripController.update_trip(trip_id, payload, service, current_user)


@router.delete(
    "/{trip_id}",
    response_model=MessageResponse,
    summary="Delete a trip",
)
async def delete_trip(
    trip_id: UUID,
    current_user: User = Depends(get_current_user),
    service: TripService = Depends(get_trip_service),
) -> MessageResponse:
    return await TripController.delete_trip(trip_id, service, current_user)
