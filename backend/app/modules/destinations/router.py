"""
app/modules/destinations/router.py

Destinations API Router — URL mapping and Swagger documentation.

Endpoints:
    Public  : GET /destinations/, GET /destinations/count, GET /destinations/{id}
    Admin   : POST /destinations/, PUT /destinations/{id}, PATCH /destinations/{id},
              DELETE /destinations/{id}, POST /destinations/{id}/image
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
    DestinationCountResponse,
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


# ── Dependency Factory ─────────────────────────────────────────────────────────

def get_destination_service(db: AsyncSession = Depends(get_db)) -> DestinationService:
    """Builds a DestinationService with its repository injected."""
    repository = DestinationRepository(db=db)
    return DestinationService(repository=repository)


# ── Public Endpoints ───────────────────────────────────────────────────────────

@router.get(
    "/count",
    response_model=DestinationCountResponse,
    summary="Count active destinations",
    description="Lightweight count endpoint used by the dashboard card. No auth required.",
)
async def count_destinations(
    service: DestinationService = Depends(get_destination_service),
) -> DestinationCountResponse:
    return await DestinationController.count_destinations(service)


@router.get(
    "/",
    response_model=DestinationPaginatedResponse,
    summary="Search and list destinations",
    description=(
        "Public endpoint to search destinations with text search, "
        "country filter, tag filter, alphabetical sorting, and pagination."
    ),
)
async def list_destinations(
    skip: int = Query(0, ge=0, description="Number of records to skip (offset)."),
    limit: int = Query(20, ge=1, le=100, description="Maximum records per page."),
    q: str | None = Query(None, description="Search term matched against name and description."),
    country: str | None = Query(None, description="Filter by country name (partial match)."),
    tag: str | None = Query(None, description="Filter by a specific tag."),
    sort_by: str = Query(
        "name",
        description="Sort field: name | country | avg_budget | created_at | duration_days",
    ),
    sort_desc: bool = Query(False, description="Set true for descending order."),
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
    return await DestinationController.get_destination(
        destination_id, service, is_admin=is_admin
    )


# ── Admin Endpoints ────────────────────────────────────────────────────────────

@router.post(
    "/embeddings/generate-all",
    summary="Generate vector embeddings for all destinations (Admin only)",
    description="Batch process all active destinations and generate/update vector embeddings using OpenAI.",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def generate_all_embeddings(
    service: DestinationService = Depends(get_destination_service),
) -> dict:
    return await DestinationController.generate_all_embeddings(service)


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


@router.put(
    "/{destination_id}",
    response_model=DestinationResponse,
    summary="Full update destination (Admin only)",
    description=(
        "Alias for PATCH — accepts a partial payload and updates the provided fields. "
        "Exposed as PUT to satisfy REST spec; uses the same partial-update logic."
    ),
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def put_destination(
    destination_id: UUID,
    payload: DestinationUpdateRequest,
    service: DestinationService = Depends(get_destination_service),
) -> DestinationResponse:
    return await DestinationController.update_destination(destination_id, payload, service)


@router.patch(
    "/{destination_id}",
    response_model=DestinationResponse,
    summary="Partial update destination (Admin only)",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def patch_destination(
    destination_id: UUID,
    payload: DestinationUpdateRequest,
    service: DestinationService = Depends(get_destination_service),
) -> DestinationResponse:
    return await DestinationController.update_destination(destination_id, payload, service)


@router.delete(
    "/{destination_id}",
    response_model=MessageResponse,
    summary="Soft-delete destination (Admin only)",
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
    summary="Upload destination cover image (Admin only)",
    description="Upload a hero image for the destination. Supported: JPG, PNG, WEBP.",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def upload_image(
    destination_id: UUID,
    file: UploadFile = File(...),
    service: DestinationService = Depends(get_destination_service),
) -> DestinationResponse:
    return await DestinationController.upload_image(destination_id, file, service)
