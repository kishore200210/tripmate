"""
tests/unit/trips/test_trip_api.py

API router and controller tests for the Trips module.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.main import create_application
from app.modules.auth.middleware import get_current_user
from app.modules.trips.enums import TripStatus
from app.modules.trips.router import get_trip_service
from app.modules.trips.schemas import TripPaginatedResponse, TripResponse
from app.modules.users.models import User


@pytest.fixture
def mock_user() -> User:
    user = User()
    user.id = uuid.uuid4()
    user.name = "John Doe"
    user.email = "john@example.com"
    user.is_active = True
    user.is_deleted = False
    return user


@pytest.fixture
def mock_trip_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def client(mock_user: User, mock_trip_service: AsyncMock) -> TestClient:
    app = create_application()
    
    # Override authentication and service layer dependencies
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_trip_service] = lambda: mock_trip_service
    
    with TestClient(app) as test_client:
        yield test_client


def test_list_trips_success(client: TestClient, mock_trip_service: AsyncMock, mock_user: User) -> None:
    # Setup mock return value
    trip_id = uuid.uuid4()
    mock_trip_service.get_user_trips.return_value = TripPaginatedResponse(
        items=[
            TripResponse(
                id=trip_id,
                title="Paris Voyage",
                description="Romantic trip to France",
                start_date=date.today(),
                end_date=date.today() + timedelta(days=5),
                budget=Decimal("1500.00"),
                status=TripStatus.PLANNING,
                cover_image_url=None,
                destination_id=None,
                user_id=mock_user.id
            )
        ],
        total=1,
        skip=0,
        limit=20
    )

    response = client.get("/api/v1/trips/?skip=0&limit=10&q=Paris&trip_status=planning")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Paris Voyage"

    # Verify mock was called with correct parameters
    mock_trip_service.get_user_trips.assert_called_once_with(
        mock_user, skip=0, limit=10, status=TripStatus.PLANNING, query="Paris"
    )


def test_get_trip_success(client: TestClient, mock_trip_service: AsyncMock, mock_user: User) -> None:
    trip_id = uuid.uuid4()
    mock_trip_service.get_trip.return_value = TripResponse(
        id=trip_id,
        title="Bali Beach",
        description="Relaxing by the sea",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=7),
        budget=Decimal("800.00"),
        status=TripStatus.CONFIRMED,
        cover_image_url=None,
        destination_id=None,
        user_id=mock_user.id
    )

    response = client.get(f"/api/v1/trips/{trip_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Bali Beach"
    assert data["status"] == "confirmed"
    mock_trip_service.get_trip.assert_called_once_with(trip_id, mock_user)


def test_get_trip_not_found(client: TestClient, mock_trip_service: AsyncMock, mock_user: User) -> None:
    trip_id = uuid.uuid4()
    mock_trip_service.get_trip.side_effect = ResourceNotFoundException("Trip not found.")

    response = client.get(f"/api/v1/trips/{trip_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["error"]["message"] == "Trip not found."


def test_create_trip_success(client: TestClient, mock_trip_service: AsyncMock, mock_user: User) -> None:
    trip_id = uuid.uuid4()
    mock_trip_service.create_trip.return_value = TripResponse(
        id=trip_id,
        title="Tokyo Tech Tour",
        description="Visiting Shibuya and Akihabara",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=6),
        budget=Decimal("2000.00"),
        status=TripStatus.PLANNING,
        cover_image_url=None,
        destination_id=None,
        user_id=mock_user.id
    )

    payload = {
        "title": "Tokyo Tech Tour",
        "description": "Visiting Shibuya and Akihabara",
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=6)),
        "budget": 2000.00
    }

    response = client.post("/api/v1/trips/", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "Tokyo Tech Tour"
    mock_trip_service.create_trip.assert_called_once()


def test_create_trip_validation_error_date_range(client: TestClient) -> None:
    payload = {
        "title": "Tokyo Tech Tour",
        "start_date": str(date.today() + timedelta(days=5)),
        "end_date": str(date.today()),
        "budget": 2000.00
    }

    response = client.post("/api/v1/trips/", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Verify the error detail mentions the model validator error
    assert "start_date cannot be after end_date" in response.text


def test_update_trip_success(client: TestClient, mock_trip_service: AsyncMock, mock_user: User) -> None:
    trip_id = uuid.uuid4()
    mock_trip_service.update_trip.return_value = TripResponse(
        id=trip_id,
        title="Tokyo Anime Tour",
        description="Visiting Shibuya and Akihabara",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=6),
        budget=Decimal("2500.00"),
        status=TripStatus.PLANNING,
        cover_image_url=None,
        destination_id=None,
        user_id=mock_user.id
    )

    payload = {
        "title": "Tokyo Anime Tour",
        "budget": 2500.00
    }

    response = client.patch(f"/api/v1/trips/{trip_id}", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Tokyo Anime Tour"
    assert float(data["budget"]) == 2500.00
    mock_trip_service.update_trip.assert_called_once()


def test_delete_trip_success(client: TestClient, mock_trip_service: AsyncMock, mock_user: User) -> None:
    trip_id = uuid.uuid4()
    mock_trip_service.delete_trip.return_value = None

    response = client.delete(f"/api/v1/trips/{trip_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "deleted successfully" in data["message"]
    mock_trip_service.delete_trip.assert_called_once_with(trip_id, mock_user)
