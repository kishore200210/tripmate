"""
app/modules/bookings/repository.py

Booking Repository — database access layer for bookings.
"""

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.trips.enums import BookingType
from app.modules.trips.models import Booking
from app.shared.repository import BaseRepository

logger = logging.getLogger(__name__)


class BookingRepository(BaseRepository[Booking]):
    """
    Repository for booking-specific database queries.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=Booking, db=db)

    async def get_trip_bookings(
        self, trip_id: UUID, skip: int = 0, limit: int = 20, booking_type: BookingType | None = None
    ) -> tuple[list[Booking], int]:
        """Fetch all bookings for a trip, optionally filtered by type."""
        stmt = select(Booking).where(
            Booking.trip_id == trip_id,
            Booking.is_deleted.is_(False),
        )
        count_stmt = select(func.count(Booking.id)).where(
            Booking.trip_id == trip_id,
            Booking.is_deleted.is_(False),
        )

        if booking_type:
            stmt = stmt.where(Booking.booking_type == booking_type)
            count_stmt = count_stmt.where(Booking.booking_type == booking_type)

        # Order by booked_at descending
        stmt = stmt.order_by(Booking.booked_at.desc().nulls_last())
        stmt = stmt.offset(skip).limit(limit)

        items_result = await self.db.execute(stmt)
        count_result = await self.db.execute(count_stmt)

        return list(items_result.scalars().all()), count_result.scalar_one() or 0

    async def get_by_id_and_trip(self, booking_id: UUID, trip_id: UUID) -> Booking | None:
        """Fetch a specific booking ensuring it belongs to the given trip."""
        stmt = select(Booking).where(
            Booking.id == booking_id,
            Booking.trip_id == trip_id,
            Booking.is_deleted.is_(False),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
