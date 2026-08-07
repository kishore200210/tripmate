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

router = APIRouter(prefix="/recommendations", tags=["ML Recommendations"])

@router.post("/predict", response_model=RecommendationResponse)
async def predict_recommendations(
    request: RecommendationRequest,
    db: AsyncSession = Depends(get_db),
    # Require authentication if needed, or allow open access. We'll require it.
    current_user = Depends(get_current_user) 
):
    repo = DestinationRepository(db)
    service = RecommendationService(repo)
    return await service.get_recommendations(request)
