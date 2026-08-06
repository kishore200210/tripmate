"""
app/modules/destinations/router.py

Destinations API Router — URL mapping and Swagger documentation.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.middleware import get_current_user_optional, require_role
from app.modules.auth.schemas import MessageResponse
from app.modules.destinations.controller import DestinationController
from app.modules.destinations.repository import DestinationRepository
from app.modules.destinations.schemas import (
    DestinationCreateRequest,
    DestinationPaginatedResponse,
    DestinationResponse,
    DestinationUpdateRequest,
)
from app.modules.destinations.service import DestinationService
from app.modules.users.enums import UserRole
from app.modules.users.models import User

router = APIRouter(
    prefix="/destinations",
    tags=["Destinations"],
)


# ── Dependency Factory ────────────────────────────────────────────────────────

def get_destination_service(db: AsyncSession = Depends(get_db)) -> DestinationService:
    repository = DestinationRepository(db=db)
    return DestinationService(repository=repository)


# ── Public Endpoints ──────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=DestinationPaginatedResponse,
    summary="Search and list destinations",
    description="Public endpoint to search destinations with filters, sorting, and pagination.",
)
async def list_destinations(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, description="Search term for name or description"),
    country: str | None = Query(None, description="Filter by country"),
    tag: str | None = Query(None, description="Filter by a specific tag"),
    sort_by: str = Query("name", description="Field to sort by (name, country, average_cost_per_day, created_at)"),
    sort_desc: bool = Query(False, description="Sort in descending order"),
    current_user: User | None = Depends(get_current_user_optional),
    service: DestinationService = Depends(get_destination_service),
) -> DestinationPaginatedResponse:
    is_admin = current_user is not None and current_user.role == UserRole.ADMIN
    return await DestinationController.search_destinations(
        skip=skip,
        limit=limit,
        query=q,
        country=country,
        tag=tag,
        sort_by=sort_by,
        sort_desc=sort_desc,
        service=service,
        is_admin=is_admin,
    )


@router.get(
    "/{destination_id}",
    response_model=DestinationResponse,
    summary="Get destination by ID",
)
async def get_destination(
    destination_id: UUID,
    current_user: User | None = Depends(get_current_user_optional),
    service: DestinationService = Depends(get_destination_service),
) -> DestinationResponse:
    is_admin = current_user is not None and current_user.role == UserRole.ADMIN
    return await DestinationController.get_destination(destination_id, service, is_admin=is_admin)


# ── Admin Endpoints ───────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=DestinationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create destination (Admin only)",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def create_destination(
    payload: DestinationCreateRequest,
    service: DestinationService = Depends(get_destination_service),
) -> DestinationResponse:
    return await DestinationController.create_destination(payload, service)


@router.patch(
    "/{destination_id}",
    response_model=DestinationResponse,
    summary="Update destination (Admin only)",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def update_destination(
    destination_id: UUID,
    payload: DestinationUpdateRequest,
    service: DestinationService = Depends(get_destination_service),
) -> DestinationResponse:
    return await DestinationController.update_destination(destination_id, payload, service)


@router.delete(
    "/{destination_id}",
    response_model=MessageResponse,
    summary="Delete destination (Admin only)",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def delete_destination(
    destination_id: UUID,
    service: DestinationService = Depends(get_destination_service),
) -> MessageResponse:
    return await DestinationController.delete_destination(destination_id, service)


@router.post(
    "/{destination_id}/image",
    response_model=DestinationResponse,
    summary="Upload destination image (Admin only)",
    description="Upload a cover image for the destination. Supported formats: JPG, PNG, WEBP.",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def upload_image(
    destination_id: UUID,
    file: UploadFile = File(...),
    service: DestinationService = Depends(get_destination_service),
) -> DestinationResponse:
    return await DestinationController.upload_image(destination_id, file, service)
