"""
app/modules/reviews/router.py

Reviews API Router — URL mapping and Swagger documentation.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.middleware import get_current_user
from app.modules.auth.schemas import MessageResponse
from app.modules.destinations.repository import DestinationRepository
from app.modules.reviews.controller import ReviewController
from app.modules.reviews.repository import ReviewRepository
from app.modules.reviews.schemas import (
    ReviewCreateRequest,
    ReviewPaginatedResponse,
    ReviewResponse,
    ReviewUpdateRequest,
)
from app.modules.reviews.service import ReviewService
from app.modules.users.models import User

router = APIRouter(
    tags=["Reviews"],
)


# ── Dependency Factory ────────────────────────────────────────────────────────

def get_review_service(db: AsyncSession = Depends(get_db)) -> ReviewService:
    repository = ReviewRepository(db=db)
    destination_repository = DestinationRepository(db=db)
    return ReviewService(repository=repository, destination_repository=destination_repository)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/destinations/{destination_id}/reviews",
    response_model=ReviewPaginatedResponse,
    summary="List all reviews for a destination",
)
async def list_destination_reviews(
    destination_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: ReviewService = Depends(get_review_service),
) -> ReviewPaginatedResponse:
    # This endpoint is intentionally public (no get_current_user dependency)
    return await ReviewController.get_destination_reviews(destination_id, skip=skip, limit=limit, service=service)


@router.post(
    "/destinations/{destination_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new review",
)
async def create_review(
    destination_id: UUID,
    payload: ReviewCreateRequest,
    current_user: User = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service),
) -> ReviewResponse:
    return await ReviewController.create_review(destination_id, payload, service, current_user)


@router.patch(
    "/reviews/{review_id}",
    response_model=ReviewResponse,
    summary="Update a review",
)
async def update_review(
    review_id: UUID,
    payload: ReviewUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service),
) -> ReviewResponse:
    return await ReviewController.update_review(review_id, payload, service, current_user)


@router.delete(
    "/reviews/{review_id}",
    response_model=MessageResponse,
    summary="Delete a review",
)
async def delete_review(
    review_id: UUID,
    current_user: User = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service),
) -> MessageResponse:
    return await ReviewController.delete_review(review_id, service, current_user)
