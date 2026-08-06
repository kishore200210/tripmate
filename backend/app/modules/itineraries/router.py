"""
app/modules/itineraries/router.py

Itineraries API Router — URL mapping and Swagger documentation.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.middleware import get_current_user
from app.modules.auth.schemas import MessageResponse
from app.modules.itineraries.controller import ItineraryController
from app.modules.itineraries.repository import ItineraryRepository
from app.modules.itineraries.schemas import (
    ItineraryItemCreateRequest,
    ItineraryItemResponse,
    ItineraryItemUpdateRequest,
    TimelineResponse,
)
from app.modules.itineraries.service import ItineraryService
from app.modules.trips.repository import TripRepository
from app.modules.users.models import User

router = APIRouter(
    prefix="/trips/{trip_id}/itinerary",
    tags=["Itinerary"],
)


# ── Dependency Factory ────────────────────────────────────────────────────────

def get_itinerary_service(db: AsyncSession = Depends(get_db)) -> ItineraryService:
    repository = ItineraryRepository(db=db)
    trip_repository = TripRepository(db=db)
    return ItineraryService(repository=repository, trip_repository=trip_repository)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=TimelineResponse,
    summary="Get trip timeline",
)
async def get_timeline(
    trip_id: UUID,
    current_user: User = Depends(get_current_user),
    service: ItineraryService = Depends(get_itinerary_service),
) -> TimelineResponse:
    return await ItineraryController.get_timeline(trip_id, service, current_user)


@router.post(
    "/",
    response_model=ItineraryItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add item to itinerary",
)
async def add_item(
    trip_id: UUID,
    payload: ItineraryItemCreateRequest,
    current_user: User = Depends(get_current_user),
    service: ItineraryService = Depends(get_itinerary_service),
) -> ItineraryItemResponse:
    return await ItineraryController.add_item(trip_id, payload, service, current_user)


@router.patch(
    "/{item_id}",
    response_model=ItineraryItemResponse,
    summary="Update or reorder an itinerary item",
)
async def update_item(
    trip_id: UUID,
    item_id: UUID,
    payload: ItineraryItemUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: ItineraryService = Depends(get_itinerary_service),
) -> ItineraryItemResponse:
    return await ItineraryController.update_item(trip_id, item_id, payload, service, current_user)


@router.delete(
    "/{item_id}",
    response_model=MessageResponse,
    summary="Delete an itinerary item",
)
async def delete_item(
    trip_id: UUID,
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    service: ItineraryService = Depends(get_itinerary_service),
) -> MessageResponse:
    return await ItineraryController.delete_item(trip_id, item_id, service, current_user)
