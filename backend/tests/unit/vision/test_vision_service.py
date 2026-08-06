"""
tests/unit/vision/test_vision_service.py

Unit tests for VisionService with mocked Ultralytics YOLO inference.
"""

from unittest.mock import MagicMock, patch

import pytest

import app.db.model_registry  # noqa: F401
from app.modules.vision.service import VisionService


@pytest.fixture
def dummy_image_bytes():
    # A 1x1 pixel black GIF image to simulate a valid image load in PIL
    return b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01D\x00;"


class TestVisionService:
    @pytest.mark.asyncio
    @patch("app.modules.vision.service.yolo_model")
    async def test_analyze_image_success(
        self,
        mock_yolo_model: MagicMock,
        dummy_image_bytes: bytes,
    ) -> None:
        # Mock YOLO results
        mock_result = MagicMock()
        mock_result.names = {0: "person", 1: "bicycle"}
        
        # Mock bounding box attributes exactly as YOLO outputs them
        mock_box = MagicMock()
        mock_xyxy = MagicMock()
        mock_xyxy.tolist.return_value = [10.5, 20.2, 50.1, 80.9]
        mock_box.xyxy = [mock_xyxy]
        mock_box.conf = [0.95]
        mock_box.cls = [0]
        
        mock_result.boxes = [mock_box]
        
        mock_yolo_model.predict.return_value = [mock_result]
        
        service = VisionService()
        response = await service.analyze_image("test.jpg", dummy_image_bytes)
        
        assert response.filename == "test.jpg"
        assert len(response.detections) == 1
        
        det = response.detections[0]
        assert det.label == "person"
        assert det.confidence == 0.9500
        assert det.box.x_min == 10.5
        assert det.box.y_max == 80.9
        
        mock_yolo_model.predict.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.modules.vision.service.yolo_model", None)
    async def test_analyze_image_model_not_loaded(
        self,
        dummy_image_bytes: bytes,
    ) -> None:
        service = VisionService()
        
        with pytest.raises(Exception) as excinfo:
            await service.analyze_image("test.jpg", dummy_image_bytes)
            
        assert "YOLO model failed to load" in str(excinfo.value)
