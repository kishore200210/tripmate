"""
app/modules/recommendations/model_loader.py
Singleton loader for the machine learning model.
"""
import os
import joblib
import logging

logger = logging.getLogger(__name__)

class ModelLoader:
    _model = None
    
    @classmethod
    def load(cls):
        if cls._model is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            model_path = os.path.join(base_dir, "models", "recommendation_model.joblib")
            
            try:
                cls._model = joblib.load(model_path)
                logger.info(f"Loaded ML model from {model_path}")
            except Exception as e:
                logger.error(f"Failed to load ML model: {e}")
                # Don't crash, let it gracefully fail later or run without ML
    
    @classmethod
    def get_model(cls):
        if cls._model is None:
            cls.load()
        return cls._model
