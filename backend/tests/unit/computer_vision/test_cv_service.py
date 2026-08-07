import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.modules.computer_vision.predictor import CVService
from app.modules.computer_vision.schemas import CVAnalysisResponse
from PIL import Image
import io

@pytest.fixture
def mock_dest_repo():
    repo = AsyncMock()
    repo.db = AsyncMock()
    return repo

@pytest.fixture
def dummy_image():
    img = Image.new('RGB', (10, 10), color='red')
    b = io.BytesIO()
    img.save(b, format='JPEG')
    return b.getvalue()

@pytest.mark.asyncio
async def test_analyze_image_success(mock_dest_repo, dummy_image):
    service = CVService(mock_dest_repo)
    
    with patch("app.modules.computer_vision.predictor.YoloModelLoader") as mock_loader:
        mock_model = MagicMock()
        
        # Mock YOLO results
        mock_result = MagicMock()
        mock_result.probs.top5 = [0, 1, 2, 3, 4]
        mock_result.probs.top5conf.tolist.return_value = [0.95, 0.02, 0.01, 0.01, 0.01]
        
        # We simulate "suspension_bridge" being detected
        mock_result.names = {0: "suspension_bridge", 1: "bridge", 2: "water", 3: "sky", 4: "car"}
        
        mock_model.predict.return_value = [mock_result]
        mock_loader.get_model.return_value = mock_model
        
        # Mock DB response
        mock_db_result = MagicMock()
        mock_dest = MagicMock()
        import uuid
        mock_dest.id = uuid.uuid4()
        mock_dest.name = "Sydney"
        mock_dest.country = "Australia"
        mock_dest.image_url = None
        mock_db_result.scalars().all.return_value = [mock_dest]
        mock_dest_repo.db.execute.return_value = mock_db_result
        
        response = await service.analyze_image(dummy_image)
        
        assert response.landmark == "Suspension Bridge"
        assert response.confidence == 95.0
        assert "Sydney" in [d.name for d in response.related_destinations]
