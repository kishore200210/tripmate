"""
app/modules/destinations/repository.py

Destination Repository — advanced database querying including search, filter, and sort.
"""

import logging
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.destinations.models import Destination
from app.shared.repository import BaseRepository

logger = logging.getLogger(__name__)


class DestinationRepository(BaseRepository[Destination]):
    """Repository for destination-specific database queries."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(model=Destination, db=db)

    async def search(
        self,
        skip: int = 0,
        limit: int = 20,
        query: str | None = None,
        country: str | None = None,
        tag: str | None = None,
        sort_by: str = "name",
        sort_desc: bool = False,
        include_inactive: bool = False,
    ) -> tuple[list[Destination], int]:
        """
        Advanced search with text query, country filter, tag filter, sorting, and pagination.
        Returns a (items, total_count) tuple — total reflects the filtered count, not the page size.
        """
        stmt = select(Destination).where(Destination.is_deleted.is_(False))
        count_stmt = select(func.count(Destination.id)).where(
            Destination.is_deleted.is_(False)
        )

        if query:
            q_clean = query.strip()
            if q_clean:
                pattern = f"%{q_clean}%"
                search_filter = or_(
                    Destination.name.ilike(pattern),
                    Destination.country.ilike(pattern),
                    Destination.city.ilike(pattern),
                    Destination.description.ilike(pattern),
                    func.array_to_string(Destination.tags, " ").ilike(pattern),
                )
                stmt = stmt.where(search_filter)
                count_stmt = count_stmt.where(search_filter)

        if country:
            country_filter = Destination.country.ilike(f"%{country}%")
            stmt = stmt.where(country_filter)
            count_stmt = count_stmt.where(country_filter)

        if tag:
            # PostgreSQL ARRAY ANY — matches destinations where tags contains the value.
            tag_filter = Destination.tags.any(tag)
            stmt = stmt.where(tag_filter)
            count_stmt = count_stmt.where(tag_filter)

        # Sort — column validated by service layer to prevent injection.
        sort_column = getattr(Destination, sort_by, Destination.name)
        stmt = stmt.order_by(sort_column.desc() if sort_desc else sort_column.asc())

        # Paginate.
        stmt = stmt.offset(skip).limit(limit)

        items_result = await self.db.execute(stmt)
        count_result = await self.db.execute(count_stmt)

        items = list(items_result.scalars().all())
        total = count_result.scalar_one() or 0

        return items, total

    async def name_exists(self, name: str, exclude_id: UUID | None = None) -> bool:
        """Check if a destination with this exact name already exists (case-insensitive)."""
        stmt = select(Destination.id).where(
            Destination.name.ilike(name.strip()),
            Destination.is_deleted.is_(False),
        )
        if exclude_id:
            stmt = stmt.where(Destination.id != exclude_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_count(self) -> int:
        """Return the total count of active (non-deleted) destinations. Used by dashboard."""
        stmt = select(func.count(Destination.id)).where(
            Destination.is_deleted.is_(False)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one() or 0

    async def vector_search(
        self,
        query_embedding: list[float],
        skip: int = 0,
        limit: int = 20,
        country: str | None = None,
        tag: str | None = None,
    ) -> tuple[list[tuple[Destination, float]], int]:
        """
        Perform a pgvector cosine similarity search across destinations.
        Returns a tuple of ((destination, similarity_score), total_count).
        """
        if not query_embedding:
            return [], 0

        # Cosine distance in pgvector
        distance_expr = Destination.embedding.cosine_distance(query_embedding)
        # Cosine similarity = 1 - distance
        similarity_expr = (1.0 - distance_expr).label("similarity_score")

        stmt = select(Destination, similarity_expr).where(
            Destination.is_deleted.is_(False),
            Destination.embedding.isnot(None),
        )
        count_stmt = select(func.count(Destination.id)).where(
            Destination.is_deleted.is_(False),
            Destination.embedding.isnot(None),
        )

        if country:
            country_filter = Destination.country.ilike(f"%{country}%")
            stmt = stmt.where(country_filter)
            count_stmt = count_stmt.where(country_filter)

        if tag:
            tag_filter = Destination.tags.any(tag)
            stmt = stmt.where(tag_filter)
            count_stmt = count_stmt.where(tag_filter)

        stmt = stmt.order_by(distance_expr.asc()).offset(skip).limit(limit)

        items_result = await self.db.execute(stmt)
        count_result = await self.db.execute(count_stmt)

        items = [(row[0], float(row[1])) for row in items_result.all()]
        total = count_result.scalar_one() or 0

        return items, total

    async def get_all_active_destinations(self) -> list[Destination]:
        """Return all active (non-deleted) destinations for embedding generation."""
        stmt = select(Destination).where(Destination.is_deleted.is_(False))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
