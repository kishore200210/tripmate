"""
app/modules/reviews/controller.py

Review Controller — thin HTTP translation layer for reviews.
"""

from uuid import UUID

from app.modules.auth.schemas import MessageResponse
from app.modules.reviews.schemas import (
    ReviewCreateRequest,
    ReviewPaginatedResponse,
    ReviewResponse,
    ReviewUpdateRequest,
)
from app.modules.reviews.service import ReviewService
from app.modules.users.models import User


class ReviewController:
    """Thin HTTP controller for the Reviews module."""

    @staticmethod
    async def get_destination_reviews(
        destination_id: UUID, skip: int, limit: int, service: ReviewService
    ) -> ReviewPaginatedResponse:
        return await service.get_destination_reviews(destination_id, skip=skip, limit=limit)

    @staticmethod
    async def create_review(
        destination_id: UUID, payload: ReviewCreateRequest, service: ReviewService, current_user: User
    ) -> ReviewResponse:
        return await service.create_review(destination_id, payload, current_user)

    @staticmethod
    async def update_review(
        review_id: UUID, payload: ReviewUpdateRequest, service: ReviewService, current_user: User
    ) -> ReviewResponse:
        return await service.update_review(review_id, payload, current_user)

    @staticmethod
    async def delete_review(
        review_id: UUID, service: ReviewService, current_user: User
    ) -> MessageResponse:
        await service.delete_review(review_id, current_user)
        return MessageResponse(message="Review deleted successfully.")
