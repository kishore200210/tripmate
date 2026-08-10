"""
app/modules/recommendations/service.py
Service layer for the recommendation engine.
"""
import pandas as pd
import numpy as np
from sqlalchemy import select
from app.modules.recommendations.schemas import RecommendationRequest, RecommendationResponse, RecommendedDestination
from app.modules.recommendations.model_loader import ModelLoader
from app.modules.destinations.repository import DestinationRepository
from app.modules.destinations.models import Destination

class RecommendationService:
    def __init__(self, destination_repo: DestinationRepository):
        self.destination_repo = destination_repo

    async def get_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        model = ModelLoader.get_model()
        if not model:
            raise Exception("Machine learning model is not loaded or unavailable.")
        
        # Convert request to pandas DataFrame to match training data
        input_data = pd.DataFrame([{
            "budget": request.budget,
            "duration": request.duration,
            "travelers": request.travelers,
            "climate": request.climate,
            "travel_style": request.travel_style,
            "season": request.season,
            "family_friendly": request.family_friendly,
            "adventure": request.adventure,
            "luxury": request.luxury
        }])
        
        # Predict probabilities
        probabilities = model.predict_proba(input_data)[0]
        classes = model.classes_
        
        # Get top 5 indices
        top_indices = np.argsort(probabilities)[::-1][:5]
        
        top_destinations = []
        for idx in top_indices:
            dest_name = classes[idx]
            conf = probabilities[idx]
            
            # Fetch from DB
            db_dest = await self._get_destination_by_name(dest_name)
            
            # Formulate reason
            reason = self._generate_reason(dest_name, conf, request)
            
            top_destinations.append(RecommendedDestination(
                id=db_dest.id if db_dest else None,
                name=dest_name,
                country=db_dest.country if db_dest else "Unknown",
                image_url=db_dest.image_url if db_dest else None,
                confidence_score=round(conf * 100, 1),
                reason=reason
            ))
            
        return RecommendationResponse(recommendations=top_destinations)
        
    async def _get_destination_by_name(self, name: str) -> Destination | None:
        stmt = select(Destination).where(Destination.name == name).limit(1)
        result = await self.destination_repo.db.execute(stmt)
        return result.scalars().first()

    def _generate_reason(self, dest_name: str, confidence: float, req: RecommendationRequest) -> str:
        travelers_text = f" for {req.travelers} traveler{'s' if req.travelers > 1 else ''}"
        if confidence > 0.8:
            return f"Highly recommended because it perfectly matches your {req.travel_style.lower()} style and {req.climate.lower()} climate preference{travelers_text}."
        elif confidence > 0.5:
            return f"A strong match for your {req.budget} USD daily budget{travelers_text} and {req.season.lower()} timing."
        else:
            return f"An alternative option that balances your preferences uniquely{travelers_text}."
