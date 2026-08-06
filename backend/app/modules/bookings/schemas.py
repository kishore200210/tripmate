"""
app/modules/bookings/schemas.py

Pydantic v2 schemas for the Bookings module.
"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.trips.enums import BookingStatus, BookingType
from app.modules.users.schemas import PaginatedResponse


class BookingCreateRequest(BaseModel):
    """Schema for POST /api/v1/trips/{trip_id}/bookings"""
    booking_type: BookingType = Field(...)
    provider: str | None = Field(None, max_length=200)
    cost: Decimal | None = Field(None, ge=0, max_digits=10, decimal_places=2)
    status: BookingStatus = Field(default=BookingStatus.PENDING)
    confirmation_ref: str | None = Field(None, max_length=100)
    notes: str | None = Field(None)
    booked_at: date | None = Field(None)


class BookingUpdateRequest(BaseModel):
    """Schema for PATCH /api/v1/trips/{trip_id}/bookings/{booking_id}"""
    booking_type: BookingType | None = Field(None)
    provider: str | None = Field(None, max_length=200)
    cost: Decimal | None = Field(None, ge=0, max_digits=10, decimal_places=2)
    status: BookingStatus | None = Field(None)
    confirmation_ref: str | None = Field(None, max_length=100)
    notes: str | None = Field(None)
    booked_at: date | None = Field(None)


class BookingResponse(BaseModel):
    """Safe representation of a Booking for API responses."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trip_id: UUID
    booking_type: BookingType
    provider: str | None
    cost: Decimal | None
    status: BookingStatus
    confirmation_ref: str | None
    notes: str | None
    booked_at: date | None


class BookingPaginatedResponse(PaginatedResponse[BookingResponse]):
    """Response schema for GET /api/v1/trips/{trip_id}/bookings."""
    pass
