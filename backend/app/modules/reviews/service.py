"""
app/modules/reviews/service.py

Review Service — business logic for review management.
"""

import logging
import uuid
from uuid import UUID

from app.core.exceptions import (
    BusinessRuleViolationException,
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
)
from app.modules.destinations.repository import DestinationRepository
from app.modules.reviews.repository import ReviewRepository
from app.modules.reviews.schemas import (
    ReviewCreateRequest,
    ReviewPaginatedResponse,
    ReviewResponse,
    ReviewUpdateRequest,
)
from app.modules.destinations.models import Review
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from app.shared.service import BaseService

logger = logging.getLogger(__name__)


class ReviewService(BaseService[ReviewRepository]):
    """Service layer for review operations."""

    def __init__(
        self, repository: ReviewRepository, destination_repository: DestinationRepository
    ) -> None:
        super().__init__(repository=repository)
        self.destination_repository = destination_repository

    async def get_destination_reviews(
        self, destination_id: UUID, skip: int = 0, limit: int = 20
    ) -> ReviewPaginatedResponse:
        """Fetch all reviews for a destination and calculate its average rating."""
        # Ensure destination exists
        dest = await self.destination_repository.get_by_id(destination_id)
        if not dest or dest.is_deleted:
            raise ResourceNotFoundException("Destination not found.")

        items, total = await self.repository.get_destination_reviews(
            destination_id=destination_id, skip=skip, limit=limit
        )
        average = await self.repository.get_average_rating(destination_id)
        
        return ReviewPaginatedResponse(
            items=[ReviewResponse.model_validate(item) for item in items],
            total=total,
            skip=skip,
            limit=limit,
            average_rating=average,
        )

    async def create_review(
        self, destination_id: UUID, payload: ReviewCreateRequest, current_user: User
    ) -> ReviewResponse:
        """Create a new review, enforcing the one-review-per-user rule."""
        logger.info("ReviewService.create_review: dest_id=%s user_id=%s", destination_id, current_user.id)
        
        # Verify destination
        dest = await self.destination_repository.get_by_id(destination_id)
        if not dest or dest.is_deleted:
            raise ResourceNotFoundException("Destination not found.")

        # Check for duplication (UniqueConstraint in DB)
        existing = await self.repository.get_user_review_for_destination(
            user_id=current_user.id, destination_id=destination_id
        )
        if existing:
            raise ResourceAlreadyExistsException("You have already reviewed this destination.")

        review = Review(
            id=uuid.uuid4(),
            user_id=current_user.id,
            destination_id=destination_id,
            rating=payload.rating,
            comment=payload.comment.strip() if payload.comment else None,
        )

        created = await self.repository.create(review)
        return ReviewResponse.model_validate(created)

    async def update_review(
        self, review_id: UUID, payload: ReviewUpdateRequest, current_user: User
    ) -> ReviewResponse:
        """Update a review, ensuring ownership."""
        logger.info("ReviewService.update_review: review_id=%s", review_id)

        review = await self.repository.get_by_id(review_id)
        if not review or review.is_deleted:
            raise ResourceNotFoundException("Review not found.")

        # Ownership check
        if review.user_id != current_user.id:
            raise BusinessRuleViolationException("You can only edit your own reviews.")

        if payload.rating is not None:
            review.rating = payload.rating
        if payload.comment is not None:
            review.comment = payload.comment.strip()

        updated = await self.repository.update(review)
        return ReviewResponse.model_validate(updated)

    async def delete_review(self, review_id: UUID, current_user: User) -> None:
        """Soft-delete a review, enforcing ownership or admin privileges."""
        logger.info("ReviewService.delete_review: review_id=%s", review_id)

        review = await self.repository.get_by_id(review_id)
        if not review or review.is_deleted:
            raise ResourceNotFoundException("Review not found.")

        # Admins can delete any review for moderation; standard users only their own
        if review.user_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise BusinessRuleViolationException("You do not have permission to delete this review.")

        review.soft_delete()
        await self.repository.update(review)
