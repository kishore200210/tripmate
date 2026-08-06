"""
schemas.py

Pydantic schemas for the ML Recommendation API.
"""

from typing import List

from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    """User preferences for generating destination recommendations."""
    budget: float = Field(..., ge=1, le=5, description="Budget scale 1 (cheap) to 5 (luxury)")
    climate: int = Field(..., ge=1, le=5, description="Climate scale 1 (cold) to 5 (hot)")
    activity_level: int = Field(..., ge=1, le=5, description="Activity scale 1 (relaxed) to 5 (intense)")


class DestinationItem(BaseModel):
    id: str
    name: str


class RecommendationResponse(BaseModel):
    """List of recommended destinations."""
    recommendations: List[DestinationItem]
