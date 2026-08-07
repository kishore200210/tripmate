"""
app/modules/computer_vision/schemas.py
Pydantic schemas for the Computer Vision module.
"""
from pydantic import BaseModel
from typing import List
from uuid import UUID

class RelatedDestination(BaseModel):
    id: UUID
    name: str
    country: str
    image_url: str | None = None

class CVAnalysisResponse(BaseModel):
    landmark: str
    confidence: float
    description: str
    related_destinations: List[RelatedDestination]
