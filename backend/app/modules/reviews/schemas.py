"""
app/modules/reviews/schemas.py

Pydantic v2 schemas for the Reviews module.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.users.schemas import PaginatedResponse


class ReviewCreateRequest(BaseModel):
    """Schema for POST /api/v1/destinations/{destination_id}/reviews"""
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: str | None = Field(None, max_length=1000)


class ReviewUpdateRequest(BaseModel):
    """Schema for PATCH /api/v1/reviews/{review_id}"""
    rating: int | None = Field(None, ge=1, le=5, description="Rating from 1 to 5")
    comment: str | None = Field(None, max_length=1000)


class ReviewResponse(BaseModel):
    """Safe representation of a Review for API responses."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    destination_id: UUID
    rating: int
    comment: str | None


class ReviewPaginatedResponse(PaginatedResponse[ReviewResponse]):
    """Response schema for GET /api/v1/destinations/{destination_id}/reviews"""
    average_rating: float = Field(0.0, description="Average rating of the destination")
