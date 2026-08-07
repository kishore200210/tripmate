"""
app/modules/ai_agent/tools.py

LangChain tools for the AI Agent (Weather and Currency).
"""

import json
import logging
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


from app.services.weather import WeatherService
from app.services.currency import CurrencyService
from app.services.pdf import PDFService


@tool
async def get_weather_tool(location: str, date: Optional[str] = None) -> str:
    """
    Fetches the current or forecasted weather for a specific location.
    
    Args:
        location: The city and country (e.g., "Paris, France" or "Tokyo, Japan").
        date: The target date (optional, defaults to today).
    """
    logger.info(f"Executing get_weather_tool for location={location}, date={date}")
    
    result = await WeatherService.get_weather(location)
    return json.dumps(result)


@tool
async def get_currency_tool(base_currency: str, target_currency: str, amount: float) -> str:
    """
    Fetches the exchange rate and calculates the converted amount.
    
    Args:
        base_currency: The 3-letter currency code to convert from (e.g., "USD").
        target_currency: The 3-letter currency code to convert to (e.g., "EUR").
        amount: The amount of base_currency to convert.
    """
    logger.info(f"Executing get_currency_tool: {amount} {base_currency} to {target_currency}")
    
    result = await CurrencyService.convert(base_currency, target_currency, amount)
    return json.dumps(result)


@tool
def generate_itinerary_pdf_tool(destination: str, trip_name: str, dates: str, itinerary_json: str) -> str:
    """
    Generates a professional itinerary PDF in the background and returns a download link.
    
    Args:
        destination: The destination city/country.
        trip_name: Name of the trip.
        dates: Dates of the trip.
        itinerary_json: A JSON string containing an array of objects with 'title' and 'description' keys for each day, plus optional 'packing_list' and 'recommendations'.
    """
    logger.info(f"Executing generate_itinerary_pdf_tool for destination={destination}")
    
    try:
        data = {
            "destination": destination,
            "trip_name": trip_name,
            "dates": dates,
        }
        
        parsed_itinerary = json.loads(itinerary_json)
        
        if isinstance(parsed_itinerary, dict):
            data.update(parsed_itinerary)
        elif isinstance(parsed_itinerary, list):
            data["itinerary"] = parsed_itinerary
            
        link = PDFService.generate_itinerary_pdf(data)
        return json.dumps({"status": "success", "download_link": link, "message": f"Successfully generated itinerary PDF. Download at: {link}"})
    except Exception as e:
        logger.error(f"PDF tool failed: {e}")
        return json.dumps({"error": "Failed to generate PDF."})


from app.db.session import AsyncSessionLocal
from app.modules.rag.repository import DocumentRepository
from app.modules.destinations.repository import DestinationRepository
from app.modules.rag.service import RAGService
from app.modules.rag.schemas import RAGQueryRequest

@tool
async def search_knowledge_base_tool(query: str) -> str:
    """
    Search the travel knowledge base (RAG) for destination information.
    Use this for questions about food, culture, packing, or top attractions.
    """
    logger.info(f"Executing search_knowledge_base_tool for query={query}")
    try:
        async with AsyncSessionLocal() as session:
            doc_repo = DocumentRepository(session)
            dest_repo = DestinationRepository(session)
            rag_service = RAGService(repository=doc_repo, destination_repository=dest_repo)
            result = await rag_service.query_knowledge_base(RAGQueryRequest(query=query))
            return json.dumps({"answer": result.answer, "sources": result.sources})
    except Exception as e:
        logger.error(f"RAG tool failed: {e}")
        return json.dumps({"error": "Failed to query knowledge base."})


from app.modules.recommendations.service import RecommendationService
from app.modules.recommendations.schemas import RecommendationRequest

@tool
async def get_ml_recommendations_tool(
    budget: float,
    duration: int,
    climate: str,
    travel_style: str,
    season: str,
    family_friendly: int = 5,
    adventure: int = 5,
    luxury: int = 5
) -> str:
    """
    Get machine learning travel destination recommendations based on user preferences.
    Use this when users ask for trip ideas, destination suggestions, or places to visit.
    
    Args:
        budget: Budget per day in USD.
        duration: Duration of trip in days.
        climate: Tropical, Temperate, Cold, Arid, or Mediterranean.
        travel_style: Relaxation, Adventure, Cultural, or City.
        season: Summer, Winter, Spring, or Fall.
        family_friendly: 1-10 scale (default 5).
        adventure: 1-10 scale (default 5).
        luxury: 1-10 scale (default 5).
    """
    logger.info(f"Executing get_ml_recommendations_tool for style={travel_style}, climate={climate}")
    try:
        req = RecommendationRequest(
            budget=budget, duration=duration, climate=climate, travel_style=travel_style,
            season=season, family_friendly=family_friendly, adventure=adventure, luxury=luxury
        )
        async with AsyncSessionLocal() as session:
            dest_repo = DestinationRepository(session)
            service = RecommendationService(dest_repo)
            result = await service.get_recommendations(req)
            
            # Format nicely for the LLM
            formatted = []
            for r in result.recommendations:
                formatted.append({
                    "destination": r.name,
                    "country": r.country,
                    "confidence": f"{r.confidence_score}%",
                    "reason": r.reason
                })
            return json.dumps(formatted)
    except Exception as e:
        logger.error(f"ML Recommendation tool failed: {e}")
        return json.dumps({"error": "Failed to fetch recommendations from ML engine."})

from app.modules.computer_vision.predictor import CVService
import httpx

@tool
async def analyze_image_tool(image_url: str) -> str:
    """
    Analyze an image from a URL to detect landmarks and travel objects.
    Use this when the user asks 'Where is this?' or provides a photo URL.
    
    Args:
        image_url: A direct URL to an image file (e.g. JPG, PNG).
    """
    logger.info(f"Executing analyze_image_tool for {image_url}")
    try:
        # Download the image to memory
        async with httpx.AsyncClient() as client:
            response = await client.get(image_url, timeout=10.0)
            response.raise_for_status()
            image_bytes = response.content
            
        async with AsyncSessionLocal() as session:
            dest_repo = DestinationRepository(session)
            service = CVService(dest_repo)
            result = await service.analyze_image(image_bytes)
            
            # Format nicely for the LLM
            formatted = {
                "detected_landmark": result.landmark,
                "confidence": f"{result.confidence}%",
                "description": result.description,
                "related_destinations": [d.name for d in result.related_destinations]
            }
            return json.dumps(formatted)
    except Exception as e:
        logger.error(f"CV analyze image tool failed: {e}")
        return json.dumps({"error": f"Failed to analyze image at {image_url}. Ensure it is a valid image link."})
