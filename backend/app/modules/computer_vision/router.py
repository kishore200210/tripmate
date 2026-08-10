"""
app/modules/computer_vision/router.py
API router for the Computer Vision module.
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.destinations.repository import DestinationRepository
from app.modules.computer_vision.predictor import CVService
from app.modules.computer_vision.schemas import CVAnalysisResponse
from app.modules.auth.middleware import get_current_user

from app.core.rate_limit import RateLimiter
from app.core.config import settings

ai_rate_limiter = RateLimiter(limit=settings.AI_RATE_LIMIT_PER_MINUTE)

# The import was fixed below (avoid getting Pydantic validation errors on module load if we got it wrong)
from app.modules.auth.middleware import get_current_user

router = APIRouter(prefix="/computer-vision", tags=["Computer Vision"])

@router.post("/analyze", response_model=CVAnalysisResponse)
async def analyze_image_endpoint(
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _rate_limit: None = Depends(ai_rate_limiter),
):
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")
        
    try:
        contents = await image.read()
        repo = DestinationRepository(db)
        service = CVService(repo)
        return await service.analyze_image(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
