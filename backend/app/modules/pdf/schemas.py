"""
app/modules/pdf/schemas.py

Pydantic v2 schemas for the PDF module.
"""

from typing import Any
from pydantic import BaseModel, Field


class TaskResponse(BaseModel):
    """Schema for POST /api/v1/pdf/itinerary/{trip_id}"""
    task_id: str = Field(..., description="The Celery task ID")
    message: str = Field(..., description="Status message")


class TaskStatusResponse(BaseModel):
    """Schema for GET /api/v1/pdf/status/{task_id}"""
    task_id: str
    status: str = Field(..., description="Task status (PENDING, SUCCESS, FAILURE, etc.)")
    result: Any | None = Field(None, description="Result data or error message")
