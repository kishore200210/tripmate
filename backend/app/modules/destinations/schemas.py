"""
app/modules/destinations/schemas.py

Pydantic v2 schemas for the Destinations module.

Schemas:
    - DestinationCreateRequest: POST body (Admin only).
    - DestinationUpdateRequest: PATCH/PUT body (Admin only, all fields optional).
    - DestinationResponse: Safe public representation returned by all endpoints.
    - DestinationPaginatedResponse: Wraps DestinationResponse for list endpoints.
    - DestinationCountResponse: Lightweight count for the dashboard.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.users.schemas import PaginatedResponse


class DestinationCreateRequest(BaseModel):
    """Schema for POST /api/v1/destinations (Admin only)."""

    name: str = Field(..., min_length=2, max_length=200)
    country: str = Field(..., min_length=2, max_length=100)
    city: str | None = Field(None, max_length=100, description="City within the country.")
    description: str = Field(..., min_length=10)
    image_url: str | None = Field(None, max_length=500, description="Hero image URL.")
    best_time_to_visit: str | None = Field(
        None, max_length=200, description="E.g. 'March–May' or 'Year-round'."
    )
    avg_budget: Decimal | None = Field(
        None, ge=0, max_digits=10, decimal_places=2,
        description="Average daily budget in USD.",
    )
    duration_days: int | None = Field(
        None, ge=1, le=365, description="Recommended trip duration in days."
    )
    tags: list[str] = Field(default_factory=list, description="Topic tags for ML recommender.")


class DestinationUpdateRequest(BaseModel):
    """Schema for PATCH /api/v1/destinations/{id} (Admin only). All fields optional."""

    name: str | None = Field(None, min_length=2, max_length=200)
    country: str | None = Field(None, min_length=2, max_length=100)
    city: str | None = Field(None, max_length=100)
    description: str | None = Field(None, min_length=10)
    image_url: str | None = Field(None, max_length=500)
    best_time_to_visit: str | None = Field(None, max_length=200)
    avg_budget: Decimal | None = Field(None, ge=0, max_digits=10, decimal_places=2)
    duration_days: int | None = Field(None, ge=1, le=365)
    tags: list[str] | None = Field(None)


class DestinationResponse(BaseModel):
    """Full public representation of a Destination returned by all read endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    country: str
    city: str | None
    description: str | None
    image_url: str | None
    best_time_to_visit: str | None
    avg_budget: Decimal | None
    duration_days: int | None
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime


class DestinationPaginatedResponse(PaginatedResponse[DestinationResponse]):
    """Response schema for GET /api/v1/destinations."""
    pass


class DestinationCountResponse(BaseModel):
    """Lightweight count response for the dashboard card."""
    total: int
