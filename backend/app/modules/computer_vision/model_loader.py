"""
app/modules/computer_vision/model_loader.py
Singleton loader for the Ultralytics YOLO vision model.
"""
import logging
from ultralytics import YOLO
import os

logger = logging.getLogger(__name__)

class YoloModelLoader:
    _model = None
    
    @classmethod
    def load(cls):
        if cls._model is None:
            try:
                # Download and load the pre-trained ImageNet classifier
                # We use yolov8n-cls.pt (nano size) for fast CPU inference.
                # It will automatically download to the local directory.
                cls._model = YOLO('yolov8n-cls.pt')
                logger.info("Loaded YOLOv8 classification model successfully.")
            except Exception as e:
                logger.error(f"Failed to load YOLO model: {e}")
    
    @classmethod
    def get_model(cls) -> YOLO:
        if cls._model is None:
            cls.load()
        return cls._model
