"""
app/modules/vision/schemas.py

Pydantic schemas for the Computer Vision module.
"""

from typing import List

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Coordinates of a detected object bounding box."""
    x_min: float
    y_min: float
    x_max: float
    y_max: float


class DetectionItem(BaseModel):
    """A single object detected in the image."""
    label: str = Field(..., description="The predicted class label.")
    confidence: float = Field(..., description="Confidence score from 0 to 1.")
    box: BoundingBox


class DetectionResponse(BaseModel):
    """Response containing all detected objects."""
    filename: str
    message: str = "Image processed successfully."
    detections: List[DetectionItem]
