"""
app/modules/trips/repository.py

Trip Repository — database access layer for trip operations.
"""

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.trips.enums import TripStatus
from app.modules.trips.models import Trip
from app.shared.repository import BaseRepository

logger = logging.getLogger(__name__)


class TripRepository(BaseRepository[Trip]):
    """
    Repository for trip-specific database queries.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=Trip, db=db)

    async def get_user_trip(self, trip_id: UUID, user_id: UUID) -> Trip | None:
        """Fetch a specific trip making sure it belongs to the user."""
        stmt = select(Trip).where(
            Trip.id == trip_id,
            Trip.user_id == user_id,
            Trip.is_deleted.is_(False),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_trips(
        self, user_id: UUID, skip: int = 0, limit: int = 20, status: TripStatus | None = None
    ) -> tuple[list[Trip], int]:
        """Fetch all trips for a specific user with optional status filtering."""
        stmt = select(Trip).where(
            Trip.user_id == user_id,
            Trip.is_deleted.is_(False),
        )
        count_stmt = select(func.count(Trip.id)).where(
            Trip.user_id == user_id,
            Trip.is_deleted.is_(False),
        )

        if status:
            stmt = stmt.where(Trip.status == status)
            count_stmt = count_stmt.where(Trip.status == status)

        # Order by start date
        stmt = stmt.order_by(Trip.start_date.asc().nulls_last())
        stmt = stmt.offset(skip).limit(limit)

        items_result = await self.db.execute(stmt)
        count_result = await self.db.execute(count_stmt)

        return list(items_result.scalars().all()), count_result.scalar_one() or 0
