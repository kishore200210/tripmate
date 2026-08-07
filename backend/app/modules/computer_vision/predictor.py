"""
app/modules/computer_vision/predictor.py
Service to predict landmarks from an image and map them to destinations.
"""
from PIL import Image
from io import BytesIO
from sqlalchemy import select
import logging

from app.modules.computer_vision.schemas import CVAnalysisResponse, RelatedDestination
from app.modules.computer_vision.model_loader import YoloModelLoader
from app.modules.destinations.repository import DestinationRepository
from app.modules.destinations.models import Destination

logger = logging.getLogger(__name__)

# A simple mapping of ImageNet classes to TripMate destinations and descriptions
IMAGENET_TRAVEL_MAP = {
    "suspension_bridge": {
        "description": "Suspension bridges are engineering marvels spanning bodies of water. Famous examples include the Golden Gate Bridge and the Sydney Harbour Bridge.",
        "destinations": ["Sydney", "New York", "San Francisco"]
    },
    "palace": {
        "description": "A grand residence, often associated with royalty. Palaces are prominent in historically rich cities.",
        "destinations": ["Paris", "Kyoto", "London"]
    },
    "alp": {
        "description": "High mountain ranges, typically associated with snow-capped peaks, skiing, and breathtaking vistas.",
        "destinations": ["Swiss Alps", "Banff", "Queenstown"]
    },
    "volcano": {
        "description": "A rupture in the crust of a planetary-mass object. Often associated with tropical or geothermal regions.",
        "destinations": ["Bali", "Tokyo", "Reykjavik"]
    },
    "triumphal_arch": {
        "description": "A monumental structure in the shape of an archway with one or more arched passageways.",
        "destinations": ["Paris", "Rome", "Barcelona"]
    },
    "church": {
        "description": "A prominent building used for religious activities, often featuring intricate architecture.",
        "destinations": ["Rome", "Paris", "Barcelona"]
    },
    "castle": {
        "description": "A type of fortified structure built during the Middle Ages by nobility.",
        "destinations": ["London", "Prague", "Rome"]
    },
    "valley": {
        "description": "A low area of land between hills or mountains, typically with a river or stream flowing through it.",
        "destinations": ["Swiss Alps", "Banff", "Queenstown"]
    },
    "seashore": {
        "description": "An area of sandy, stony, or rocky land bordering and level with the sea.",
        "destinations": ["Maldives", "Goa", "Bali", "Maui"]
    },
    "coral_reef": {
        "description": "An underwater ecosystem characterized by reef-building corals. Great for scuba diving.",
        "destinations": ["Maldives", "Bali", "Sydney"]
    }
}

class CVService:
    def __init__(self, dest_repo: DestinationRepository):
        self.dest_repo = dest_repo
        
    async def analyze_image(self, image_bytes: bytes) -> CVAnalysisResponse:
        model = YoloModelLoader.get_model()
        if not model:
            raise Exception("Computer Vision model is not loaded.")
            
        try:
            image = Image.open(BytesIO(image_bytes)).convert("RGB")
            
            # Run inference
            results = model.predict(source=image, verbose=False)
            
            # YOLOv8 classification output
            top5_probs = results[0].probs.top5
            top5_confs = results[0].probs.top5conf.tolist()
            
            # Find the best travel-related class
            matched_class = None
            matched_conf = 0.0
            
            for class_idx, conf in zip(top5_probs, top5_confs):
                class_name = results[0].names[class_idx]
                
                # Check if it's in our travel map, or just fall back to the top-1
                if class_name in IMAGENET_TRAVEL_MAP:
                    matched_class = class_name
                    matched_conf = conf
                    break
                    
            if not matched_class:
                # Fallback to top-1 if no travel-specific class found
                matched_class = results[0].names[top5_probs[0]]
                matched_conf = top5_confs[0]
                
            # Formatting the class name (e.g., "suspension_bridge" -> "Suspension Bridge")
            formatted_name = matched_class.replace("_", " ").title()
            
            # Default fallback description and destinations if not in map
            description = f"We detected a {formatted_name} in your photo. Explore the world to discover beautiful sights like this!"
            target_dest_names = []
            
            if matched_class in IMAGENET_TRAVEL_MAP:
                description = IMAGENET_TRAVEL_MAP[matched_class]["description"]
                target_dest_names = IMAGENET_TRAVEL_MAP[matched_class]["destinations"]
                
            # Fetch related destinations from the DB
            related_dests = []
            if target_dest_names:
                stmt = select(Destination).where(Destination.name.in_(target_dest_names))
                db_results = await self.dest_repo.db.execute(stmt)
                db_dests = db_results.scalars().all()
                
                for d in db_dests:
                    related_dests.append(RelatedDestination(
                        id=d.id,
                        name=d.name,
                        country=d.country,
                        image_url=d.image_url
                    ))
                    
            return CVAnalysisResponse(
                landmark=formatted_name,
                confidence=round(matched_conf * 100, 1),
                description=description,
                related_destinations=related_dests
            )
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            raise Exception("Failed to analyze image. Please ensure it is a valid JPG/PNG file.")
