"""
app/modules/itineraries/repository.py

Itinerary Repository — database access layer for itinerary items.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.trips.models import ItineraryItem
from app.shared.repository import BaseRepository

logger = logging.getLogger(__name__)


class ItineraryRepository(BaseRepository[ItineraryItem]):
    """
    Repository for itinerary-specific database queries.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=ItineraryItem, db=db)

    async def get_trip_timeline(self, trip_id: UUID) -> list[ItineraryItem]:
        """Fetch all itinerary items for a specific trip, ordered by day and time."""
        stmt = (
            select(ItineraryItem)
            .where(
                ItineraryItem.trip_id == trip_id,
                ItineraryItem.is_deleted.is_(False),
            )
            .order_by(
                ItineraryItem.day_no.asc(),
                ItineraryItem.scheduled_time.asc().nulls_last(),
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id_and_trip(self, item_id: UUID, trip_id: UUID) -> ItineraryItem | None:
        """Fetch a specific itinerary item ensuring it belongs to the given trip."""
        stmt = select(ItineraryItem).where(
            ItineraryItem.id == item_id,
            ItineraryItem.trip_id == trip_id,
            ItineraryItem.is_deleted.is_(False),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
