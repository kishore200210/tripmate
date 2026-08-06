"""
app/modules/vision/service.py

Computer Vision Service — integrates Ultralytics YOLO11 and OpenCV.
"""

import io
import logging

import cv2
import numpy as np
from PIL import Image

# Import YOLO. We place it inside a try block or globally.
try:
    from ultralytics import YOLO
    
    # Load model globally to avoid reloading on every request
    # yolo11n.pt is the nano model, very fast and lightweight.
    # It will auto-download weights on first run if not present.
    yolo_model = YOLO("yolo11n.pt")
except ImportError:
    yolo_model = None

from app.core.exceptions import ValidationException
from app.modules.vision.schemas import BoundingBox, DetectionItem, DetectionResponse

logger = logging.getLogger(__name__)


class VisionService:
    """Service layer for running computer vision inference."""

    @staticmethod
    async def analyze_image(filename: str, file_bytes: bytes) -> DetectionResponse:
        """Runs YOLO11 inference on an uploaded image stream."""
        if yolo_model is None:
            raise ValidationException("YOLO model failed to load. Check dependencies.")

        try:
            # 1. Convert bytes to PIL Image
            image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            
            # 2. Convert PIL Image to OpenCV format (numpy array)
            # OpenCV uses BGR natively, but YOLO can handle RGB if passed as np array directly.
            # We'll stick to standard numpy conversion.
            img_array = np.array(image)
            
            # 3. Run Inference
            # YOLO returns a list of Results objects (one for each image, we only passed one)
            results = yolo_model.predict(img_array, conf=0.25)
            
            if not results:
                return DetectionResponse(filename=filename, detections=[])
                
            result = results[0]
            boxes = result.boxes
            names = result.names
            
            # 4. Map results to structured response schema
            detections = []
            if boxes is not None:
                for box in boxes:
                    # coords are [x_min, y_min, x_max, y_max]
                    coords = box.xyxy[0].tolist() 
                    conf = float(box.conf[0])
                    class_id = int(box.cls[0])
                    label = names[class_id]
                    
                    bbox = BoundingBox(
                        x_min=round(coords[0], 2),
                        y_min=round(coords[1], 2),
                        x_max=round(coords[2], 2),
                        y_max=round(coords[3], 2),
                    )
                    
                    detections.append(
                        DetectionItem(
                            label=label,
                            confidence=round(conf, 4),
                            box=bbox
                        )
                    )
            
            return DetectionResponse(
                filename=filename,
                detections=detections
            )

        except Exception as e:
            logger.error("Vision Inference Error: %s", str(e))
            raise ValidationException(f"Failed to process image: {str(e)}")
