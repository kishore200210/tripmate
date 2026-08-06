"""
app/modules/vision/controller.py

Vision Controller — HTTP translation layer for the Vision service.
"""

from fastapi import UploadFile

from app.core.exceptions import ValidationException
from app.modules.vision.schemas import DetectionResponse
from app.modules.vision.service import VisionService


class VisionController:
    """HTTP controller for the Vision module."""

    @staticmethod
    async def analyze_image(file: UploadFile, service: VisionService) -> DetectionResponse:
        """Validates the upload and streams bytes to the inference engine."""
        if not file.content_type or not file.content_type.startswith("image/"):
            raise ValidationException("Uploaded file must be an image.")
            
        # Read file bytes securely in memory
        file_bytes = await file.read()
        
        # We don't save the file to disk; we process it directly in memory for speed
        return await service.analyze_image(file.filename or "unknown.jpg", file_bytes)
