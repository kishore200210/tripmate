"""
tests/unit/analytics/test_analytics.py

Unit tests for AnalyticsService and Analytics schemas.
"""

from unittest.mock import AsyncMock
import pytest

from app.modules.analytics.service import AnalyticsService
from app.modules.analytics.repository import AnalyticsRepository


@pytest.fixture
def mock_repository() -> AsyncMock:
    return AsyncMock(spec=AnalyticsRepository)


@pytest.fixture
def analytics_service(mock_repository: AsyncMock) -> AnalyticsService:
    return AnalyticsService(repository=mock_repository)


@pytest.mark.asyncio
async def test_get_dashboard_analytics_success(
    analytics_service: AnalyticsService,
    mock_repository: AsyncMock,
) -> None:
    # Setup mock returns
    mock_repository.get_summary_metrics.return_value = {
        "total_users": 100,
        "active_users": 85,
        "total_trips": 50,
        "completed_trips": 10,
        "average_trip_budget": 1200.50,
        "total_trip_budget": 60025.00,
    }
    mock_repository.get_status_distribution.return_value = {
        "planning": 20,
        "confirmed": 15,
        "ongoing": 5,
        "completed": 10,
        "cancelled": 0,
    }
    mock_repository.get_top_destinations.return_value = [
        {"name": "Paris", "country": "France", "trip_count": 12},
        {"name": "Tokyo", "country": "Japan", "trip_count": 8},
    ]
    mock_repository.get_monthly_user_registrations.return_value = [
        {"month": "2026-07", "count": 40},
        {"month": "2026-08", "count": 60},
    ]
    mock_repository.get_monthly_trip_creations.return_value = [
        {"month": "2026-07", "count": 20},
        {"month": "2026-08", "count": 30},
    ]

    result = await analytics_service.get_dashboard_analytics()

    # Assertions
    assert result.summary.total_users == 100
    assert result.summary.active_users == 85
    assert result.summary.average_trip_budget == 1200.50
    assert result.status_distribution.planning == 20
    assert len(result.top_destinations) == 2
    assert result.top_destinations[0].name == "Paris"
    assert result.top_destinations[0].trip_count == 12
    assert len(result.monthly_user_registrations) == 2
    assert result.monthly_user_registrations[0].month == "2026-07"
    assert result.monthly_user_registrations[0].count == 40
    assert len(result.monthly_trip_creations) == 2
    assert result.monthly_trip_creations[1].month == "2026-08"
    assert result.monthly_trip_creations[1].count == 30


@pytest.mark.asyncio
async def test_get_dashboard_analytics_empty_data(
    analytics_service: AnalyticsService,
    mock_repository: AsyncMock,
) -> None:
    # Setup mock returns representing empty database
    mock_repository.get_summary_metrics.return_value = {
        "total_users": 0,
        "active_users": 0,
        "total_trips": 0,
        "completed_trips": 0,
        "average_trip_budget": None,
        "total_trip_budget": None,
    }
    mock_repository.get_status_distribution.return_value = {
        "planning": 0,
        "confirmed": 0,
        "ongoing": 0,
        "completed": 0,
        "cancelled": 0,
    }
    mock_repository.get_top_destinations.return_value = []
    mock_repository.get_monthly_user_registrations.return_value = []
    mock_repository.get_monthly_trip_creations.return_value = []

    result = await analytics_service.get_dashboard_analytics()

    # Assertions
    assert result.summary.total_users == 0
    assert result.summary.average_trip_budget is None
    assert result.status_distribution.planning == 0
    assert result.top_destinations == []
    assert result.monthly_user_registrations == []
    assert result.monthly_trip_creations == []
