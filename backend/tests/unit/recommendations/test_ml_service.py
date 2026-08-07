"""
tests/unit/recommendations/test_ml_service.py
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.modules.recommendations.service import RecommendationService
from app.modules.recommendations.schemas import RecommendationRequest
import numpy as np

@pytest.fixture
def mock_dest_repo():
    repo = AsyncMock()
    repo.db = AsyncMock()
    return repo

@pytest.mark.asyncio
async def test_get_recommendations_success(mock_dest_repo):
    service = RecommendationService(mock_dest_repo)
    
    # Mock ModelLoader
    with patch("app.modules.recommendations.service.ModelLoader") as mock_loader:
        mock_model = MagicMock()
        # Simulate 3 classes
        mock_model.classes_ = np.array(["Bali", "Tokyo", "Paris"])
        # Simulate probabilities for one sample
        mock_model.predict_proba.return_value = np.array([[0.8, 0.15, 0.05]])
        
        mock_loader.get_model.return_value = mock_model
        
        # Mock destination db return
        mock_result = MagicMock()
        mock_dest = MagicMock()
        import uuid
        mock_dest.id = uuid.uuid4()
        mock_dest.country = "Mock Country"
        mock_dest.image_url = "http://mock"
        mock_result.scalars().first.return_value = mock_dest
        mock_dest_repo.db.execute.return_value = mock_result
        
        req = RecommendationRequest(
            budget=100,
            duration=7,
            climate="Tropical",
            travel_style="Relaxation",
            season="Summer",
            family_friendly=5,
            adventure=5,
            luxury=5
        )
        
        response = await service.get_recommendations(req)
        
        assert len(response.recommendations) == 3
        assert response.recommendations[0].name == "Bali"
        assert response.recommendations[0].confidence_score == 80.0
