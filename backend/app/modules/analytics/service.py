"""
app/modules/analytics/service.py

Analytics Service — coordinates repository calls to construct dashboard response payloads.
"""

from app.modules.analytics.repository import AnalyticsRepository
from app.modules.analytics.schemas import DashboardAnalyticsResponse


class AnalyticsService:
    """Service layer coordinates site-wide analytics aggregates."""

    def __init__(self, repository: AnalyticsRepository) -> None:
        self.repository = repository

    async def get_dashboard_analytics(self) -> DashboardAnalyticsResponse:
        """Collect all dashboard metrics and return a validated Pydantic model."""
        summary = await self.repository.get_summary_metrics()
        status_distribution = await self.repository.get_status_distribution()
        top_destinations = await self.repository.get_top_destinations()
        monthly_user_registrations = await self.repository.get_monthly_user_registrations()
        monthly_trip_creations = await self.repository.get_monthly_trip_creations()

        return DashboardAnalyticsResponse(
            summary=summary,
            status_distribution=status_distribution,
            top_destinations=top_destinations,
            monthly_user_registrations=monthly_user_registrations,
            monthly_trip_creations=monthly_trip_creations,
        )
