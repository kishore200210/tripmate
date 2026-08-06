"""
app/modules/reviews/repository.py

Review Repository — database access layer for user reviews.
"""

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.destinations.models import Review
from app.shared.repository import BaseRepository

logger = logging.getLogger(__name__)


class ReviewRepository(BaseRepository[Review]):
    """
    Repository for review-specific database queries.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=Review, db=db)

    async def get_destination_reviews(
        self, destination_id: UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[Review], int]:
        """Fetch all reviews for a destination with pagination."""
        stmt = select(Review).where(
            Review.destination_id == destination_id,
            Review.is_deleted.is_(False),
        )
        count_stmt = select(func.count(Review.id)).where(
            Review.destination_id == destination_id,
            Review.is_deleted.is_(False),
        )

        stmt = stmt.order_by(Review.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        items_result = await self.db.execute(stmt)
        count_result = await self.db.execute(count_stmt)

        return list(items_result.scalars().all()), count_result.scalar_one() or 0

    async def get_average_rating(self, destination_id: UUID) -> float:
        """Calculate the exact mathematical average rating for a destination."""
        stmt = select(func.avg(Review.rating)).where(
            Review.destination_id == destination_id,
            Review.is_deleted.is_(False),
        )
        result = await self.db.execute(stmt)
        avg = result.scalar_one_or_none()
        
        return round(float(avg), 1) if avg is not None else 0.0

    async def get_user_review_for_destination(
        self, user_id: UUID, destination_id: UUID
    ) -> Review | None:
        """Check for existing review to satisfy UniqueConstraint."""
        stmt = select(Review).where(
            Review.user_id == user_id,
            Review.destination_id == destination_id,
            Review.is_deleted.is_(False),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
