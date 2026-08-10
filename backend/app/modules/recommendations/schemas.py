"""
app/modules/recommendations/schemas.py
"""
from pydantic import BaseModel, Field
from typing import List
from uuid import UUID

class RecommendationRequest(BaseModel):
    budget: float = Field(..., description="Budget per day in USD")
    duration: int = Field(..., description="Duration of the trip in days")
    climate: str = Field(..., description="Preferred climate (e.g., Tropical, Temperate, Cold, Arid, Mediterranean)")
    travel_style: str = Field(..., description="Preferred travel style (e.g., Relaxation, Adventure, Cultural, City)")
    season: str = Field(..., description="Season of travel (e.g., Summer, Winter, Spring, Fall)")
    family_friendly: int = Field(..., ge=1, le=10, description="How much you care about family friendliness (1-10)")
    adventure: int = Field(..., ge=1, le=10, description="How much you care about adventure (1-10)")
    luxury: int = Field(..., ge=1, le=10, description="How much you care about luxury (1-10)")
    travelers: int = Field(1, ge=1, le=20, description="Number of travelers (1-20)")

class RecommendedDestination(BaseModel):
    id: UUID | None = None
    name: str
    country: str
    image_url: str | None = None
    confidence_score: float
    reason: str

class RecommendationResponse(BaseModel):
    recommendations: List[RecommendedDestination]
