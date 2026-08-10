"""
app/modules/recommendations/router.py
FastAPI router for the Machine Learning recommendation engine.
"""
from fastapi import APIRouter, Depends
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.destinations.repository import DestinationRepository
from app.modules.recommendations.service import RecommendationService
from app.modules.recommendations.schemas import RecommendationRequest, RecommendationResponse
from app.modules.auth.middleware import get_current_user

from app.core.rate_limit import RateLimiter
from app.core.config import settings

ai_rate_limiter = RateLimiter(limit=settings.AI_RATE_LIMIT_PER_MINUTE)

router = APIRouter(prefix="/recommendations", tags=["ML Recommendations"])

@router.post("/predict", response_model=RecommendationResponse)
async def predict_recommendations(
    request: RecommendationRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    _rate_limit: None = Depends(ai_rate_limiter),
):
    repo = DestinationRepository(db)
    service = RecommendationService(repo)
    return await service.get_recommendations(request)
