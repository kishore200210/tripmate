"""
app/modules/trips/schemas.py

Pydantic v2 schemas for the Trips module.
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.trips.enums import TripStatus
from app.modules.users.schemas import PaginatedResponse


class TripCreateRequest(BaseModel):
    """Schema for POST /api/v1/trips"""
    title: str = Field(..., min_length=2, max_length=200)
    description: str | None = Field(None)
    start_date: date | None = Field(None)
    end_date: date | None = Field(None)
    budget: Decimal | None = Field(None, ge=0, max_digits=10, decimal_places=2)
    destination_id: UUID | None = Field(None)
    place_name: str | None = Field(None, max_length=300)
    place_country: str | None = Field(None, max_length=100)

    @model_validator(mode="after")
    def validate_dates(self) -> "TripCreateRequest":
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("start_date cannot be after end_date")
        return self


class TripUpdateRequest(BaseModel):
    """Schema for PATCH /api/v1/trips/{id}"""
    title: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = Field(None)
    start_date: date | None = Field(None)
    end_date: date | None = Field(None)
    budget: Decimal | None = Field(None, ge=0, max_digits=10, decimal_places=2)
    status: TripStatus | None = Field(None)
    destination_id: UUID | None = Field(None)
    place_name: str | None = Field(None, max_length=300)
    place_country: str | None = Field(None, max_length=100)

    @model_validator(mode="after")
    def validate_dates(self) -> "TripUpdateRequest":
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("start_date cannot be after end_date")
        return self


class TripResponse(BaseModel):
    """Safe representation of a Trip for API responses."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    start_date: date | None
    end_date: date | None
    budget: Decimal | None
    status: TripStatus
    cover_image_url: str | None
    destination_id: UUID | None
    place_name: str | None
    place_country: str | None
    user_id: UUID
    created_at: datetime
    updated_at: datetime


class TripPaginatedResponse(PaginatedResponse[TripResponse]):
    """Response schema for GET /api/v1/trips."""
    pass
