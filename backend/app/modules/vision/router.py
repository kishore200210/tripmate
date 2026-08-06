"""
app/modules/vision/router.py

Vision API Router — URL mapping and Swagger documentation.
"""

from fastapi import APIRouter, Depends, File, UploadFile

from app.modules.auth.middleware import get_current_user
from app.modules.users.models import User
from app.modules.vision.controller import VisionController
from app.modules.vision.schemas import DetectionResponse
from app.modules.vision.service import VisionService

router = APIRouter(
    prefix="/vision",
    tags=["Computer Vision"],
)


# ── Dependency Factory ────────────────────────────────────────────────────────

def get_vision_service() -> VisionService:
    # No DB repository needed for Vision currently
    return VisionService()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/analyze",
    response_model=DetectionResponse,
    summary="Upload an image to detect landmarks and objects",
)
async def analyze_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: VisionService = Depends(get_vision_service),
) -> DetectionResponse:
    """
    Accepts a multipart/form-data image upload.
    Runs YOLO11 object detection in-memory.
    Returns a structured JSON schema mapping bounding boxes and labels.
    """
    return await VisionController.analyze_image(file, service)
