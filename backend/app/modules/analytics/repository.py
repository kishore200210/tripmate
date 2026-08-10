"""
app/modules/analytics/repository.py

Analytics Repository — handles database aggregations for admin dashboard analytics.
"""

import logging
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.users.models import User
from app.modules.trips.models import Trip
from app.modules.destinations.models import Destination
from app.modules.trips.enums import TripStatus

logger = logging.getLogger(__name__)


class AnalyticsRepository:
    """
    Repository for aggregating site-wide analytics metrics.
    All queries exclude soft-deleted records to maintain correctness.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_summary_metrics(self) -> dict:
        """Fetch general count and budget aggregate metrics."""
        total_users_query = select(func.count(User.id)).where(User.is_deleted.is_(False))
        active_users_query = select(func.count(User.id)).where(User.is_active.is_(True), User.is_deleted.is_(False))
        total_trips_query = select(func.count(Trip.id)).where(Trip.is_deleted.is_(False))
        completed_trips_query = select(func.count(Trip.id)).where(Trip.status == TripStatus.COMPLETED, Trip.is_deleted.is_(False))
        budget_query = select(
            func.avg(Trip.budget),
            func.sum(Trip.budget)
        ).where(Trip.is_deleted.is_(False))

        total_users = (await self.db.execute(total_users_query)).scalar_one() or 0
        active_users = (await self.db.execute(active_users_query)).scalar_one() or 0
        total_trips = (await self.db.execute(total_trips_query)).scalar_one() or 0
        completed_trips = (await self.db.execute(completed_trips_query)).scalar_one() or 0

        budget_res = (await self.db.execute(budget_query)).first()
        avg_budget = float(budget_res[0]) if budget_res and budget_res[0] is not None else None
        sum_budget = float(budget_res[1]) if budget_res and budget_res[1] is not None else None

        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_trips": total_trips,
            "completed_trips": completed_trips,
            "average_trip_budget": avg_budget,
            "total_trip_budget": sum_budget,
        }

    async def get_status_distribution(self) -> dict:
        """Fetch count of trips grouped by status."""
        query = (
            select(Trip.status, func.count(Trip.id))
            .where(Trip.is_deleted.is_(False))
            .group_by(Trip.status)
        )
        res = await self.db.execute(query)
        distribution = {status.value: count for status, count in res.all()}

        return {
            "planning": distribution.get("planning", 0),
            "confirmed": distribution.get("confirmed", 0),
            "ongoing": distribution.get("ongoing", 0),
            "completed": distribution.get("completed", 0),
            "cancelled": distribution.get("cancelled", 0),
        }

    async def get_top_destinations(self, limit: int = 5) -> list[dict]:
        """Fetch the most popular trip destinations."""
        stmt = (
            select(
                func.coalesce(Destination.name, Trip.place_name).label("name"),
                func.coalesce(Destination.country, Trip.place_country).label("country"),
                func.count(Trip.id).label("trip_count")
            )
            .outerjoin(Destination, Trip.destination_id == Destination.id)
            .where(
                Trip.is_deleted.is_(False),
                or_(
                    Trip.destination_id.isnot(None),
                    Trip.place_name.isnot(None)
                )
            )
            .group_by(
                func.coalesce(Destination.name, Trip.place_name),
                func.coalesce(Destination.country, Trip.place_country)
            )
            .order_by(func.count(Trip.id).desc())
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        return [
            {"name": name, "country": country, "trip_count": trip_count}
            for name, country, trip_count in res.all()
            if name and country
        ]

    async def get_monthly_user_registrations(self) -> list[dict]:
        """Fetch monthly user registration trends."""
        is_sqlite = self.db.bind.dialect.name == "sqlite" if self.db.bind else False
        if is_sqlite:
            month_expr = func.strftime("%Y-%m", User.created_at)
        else:
            month_expr = func.to_char(User.created_at, "YYYY-MM")

        stmt = (
            select(
                month_expr.label("month"),
                func.count(User.id).label("count")
            )
            .where(User.is_deleted.is_(False))
            .group_by(month_expr)
            .order_by("month")
        )
        res = await self.db.execute(stmt)
        return [{"month": month, "count": count} for month, count in res.all() if month]

    async def get_monthly_trip_creations(self) -> list[dict]:
        """Fetch monthly trip creation trends."""
        is_sqlite = self.db.bind.dialect.name == "sqlite" if self.db.bind else False
        if is_sqlite:
            month_expr = func.strftime("%Y-%m", Trip.created_at)
        else:
            month_expr = func.to_char(Trip.created_at, "YYYY-MM")

        stmt = (
            select(
                month_expr.label("month"),
                func.count(Trip.id).label("count")
            )
            .where(Trip.is_deleted.is_(False))
            .group_by(month_expr)
            .order_by("month")
        )
        res = await self.db.execute(stmt)
        return [{"month": month, "count": count} for month, count in res.all() if month]
