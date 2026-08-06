"""
app/modules/itineraries/schemas.py

Pydantic v2 schemas for the Itinerary module.
"""

from datetime import time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ItineraryItemCreateRequest(BaseModel):
    """Schema for POST /api/v1/trips/{trip_id}/itinerary"""
    day_no: int = Field(..., ge=1, description="Day number of the trip (1-indexed)")
    activity: str = Field(..., min_length=2, max_length=300)
    scheduled_time: time | None = Field(None, description="Time of the activity")
    notes: str | None = Field(None)
    location: str | None = Field(None, max_length=300)


class ItineraryItemUpdateRequest(BaseModel):
    """Schema for PATCH /api/v1/itinerary/{item_id}"""
    day_no: int | None = Field(None, ge=1, description="Day number of the trip (1-indexed)")
    activity: str | None = Field(None, min_length=2, max_length=300)
    scheduled_time: time | None = Field(None, description="Time of the activity")
    notes: str | None = Field(None)
    location: str | None = Field(None, max_length=300)


class ItineraryItemResponse(BaseModel):
    """Safe representation of an Itinerary Item for API responses."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trip_id: UUID
    day_no: int
    activity: str
    scheduled_time: time | None
    notes: str | None
    location: str | None


class TimelineResponse(BaseModel):
    """Represents a complete trip timeline, grouping by days or returning a sorted flat list."""
    trip_id: UUID
    items: list[ItineraryItemResponse]
    total_items: int
