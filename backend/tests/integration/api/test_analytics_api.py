"""
tests/integration/api/test_analytics_api.py

Integration tests for the Analytics API endpoints and RBAC protection.
"""

import uuid
from unittest.mock import AsyncMock
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import create_application
from app.modules.auth.middleware import get_current_user
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from app.modules.analytics.router import get_analytics_service
from app.modules.analytics.schemas import DashboardAnalyticsResponse, SummaryMetrics, StatusDistribution


@pytest.fixture
def standard_user() -> User:
    user = User()
    user.id = uuid.uuid4()
    user.name = "Standard Traveller"
    user.email = "user@example.com"
    user.role = UserRole.USER
    user.is_active = True
    user.is_deleted = False
    return user


@pytest.fixture
def admin_user() -> User:
    user = User()
    user.id = uuid.uuid4()
    user.name = "Admin Master"
    user.email = "admin@example.com"
    user.role = UserRole.ADMIN
    user.is_active = True
    user.is_deleted = False
    return user


@pytest.fixture
def mock_analytics_service() -> AsyncMock:
    return AsyncMock()


def test_get_dashboard_analytics_unauthenticated() -> None:
    """Test that unauthorized anonymous requests are rejected with 401."""
    app = create_application()
    with TestClient(app) as client:
        response = client.get("/api/v1/analytics/dashboard")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_dashboard_analytics_forbidden_for_standard_user(standard_user: User) -> None:
    """Test that standard travellers are forbidden (403) from accessing admin metrics."""
    app = create_application()
    app.dependency_overrides[get_current_user] = lambda: standard_user

    with TestClient(app) as client:
        response = client.get("/api/v1/analytics/dashboard")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Access denied." in response.json()["error"]["message"]


def test_get_dashboard_analytics_success_for_admin(
    admin_user: User,
    mock_analytics_service: AsyncMock,
) -> None:
    """Test that administrators can successfully retrieve the dashboard analytics payload."""
    app = create_application()
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_analytics_service] = lambda: mock_analytics_service

    # Setup mock return value matching schema
    mock_analytics_service.get_dashboard_analytics.return_value = DashboardAnalyticsResponse(
        summary=SummaryMetrics(
            total_users=10,
            active_users=8,
            total_trips=20,
            completed_trips=5,
            average_trip_budget=1500.0,
            total_trip_budget=30000.0,
        ),
        status_distribution=StatusDistribution(
            planning=10,
            confirmed=5,
            ongoing=0,
            completed=5,
            cancelled=0,
        ),
        top_destinations=[],
        monthly_user_registrations=[],
        monthly_trip_creations=[]
    )

    with TestClient(app) as client:
        response = client.get("/api/v1/analytics/dashboard")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["summary"]["total_users"] == 10
        assert data["summary"]["average_trip_budget"] == 1500.0
        assert data["status_distribution"]["planning"] == 10
        mock_analytics_service.get_dashboard_analytics.assert_called_once()
