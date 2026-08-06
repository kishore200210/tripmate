"""
app/modules/destinations/schemas.py

Pydantic v2 schemas for the Destinations module.
"""

from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.users.schemas import PaginatedResponse


class DestinationCreateRequest(BaseModel):
    """Schema for POST /api/v1/destinations (Admin only)."""
    name: str = Field(..., min_length=2, max_length=255)
    country: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., min_length=10)
    avg_budget: Decimal = Field(..., ge=0, max_digits=10, decimal_places=2)
    tags: list[str] = Field(default_factory=list)


class DestinationUpdateRequest(BaseModel):
    """Schema for PATCH /api/v1/destinations/{id} (Admin only)."""
    name: str | None = Field(None, min_length=2, max_length=255)
    country: str | None = Field(None, min_length=2, max_length=100)
    description: str | None = Field(None, min_length=10)
    avg_budget: Decimal | None = Field(None, ge=0, max_digits=10, decimal_places=2)
    tags: list[str] | None = Field(None)


class DestinationResponse(BaseModel):
    """Safe representation of a Destination for API responses."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    country: str
    description: str
    avg_budget: Decimal | None
    tags: list[str] | None
    image_url: str | None


class DestinationPaginatedResponse(PaginatedResponse[DestinationResponse]):
    """Response schema for GET /api/v1/destinations."""
    pass
