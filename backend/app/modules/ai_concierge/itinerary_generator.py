import json
import logging
import os
from typing import Any

from groq import AsyncGroq
from app.core.config import get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert AI Travel Concierge.
You must output ONLY valid JSON. Do not include markdown code blocks like ```json ... ```, just the raw JSON object.
Your JSON must follow this exact structure:
{
  "budget_estimate": "Detailed string about estimated costs.",
  "packing_checklist": "Stringified list or detailed string of packing items.",
  "restaurant_recommendations": "Stringified list or detailed string of local food spots.",
  "local_attractions": "Stringified list or detailed string of must-visit places.",
  "weather_suggestions": "Detailed string about expected weather and preparations.",
  "day_plans": [
    {
      "day_no": 1,
      "theme": "Theme for the day (e.g., Arrival & Culture)",
      "description": "Overview of what this day entails.",
      "activities": [
        {
          "activity": "Brief activity title",
          "scheduled_time": "14:00:00", 
          "notes": "Extra details",
          "location": "Place Name"
        }
      ]
    }
  ]
}

Note: scheduled_time must be in HH:MM:SS format or null. Ensure day_no starts at 1 and covers the requested duration.
"""

class ItineraryGenerator:
    def __init__(self):
        settings = get_settings()
        api_key = settings.GROQ_API_KEY.strip() if settings.GROQ_API_KEY else ""
        
        is_loaded = bool(api_key and api_key != "dummy-key" and api_key != "dummy-key-for-tests")
        prefix = api_key[:6] if len(api_key) >= 6 else api_key
        suffix = api_key[-4:] if len(api_key) >= 10 else ""
        logger.info(
            "ItineraryGenerator Groq Client Init — Loaded GROQ API Key: %s | Prefix: %s...%s | Length: %d",
            is_loaded, prefix, suffix, len(api_key)
        )
        
        self.client = AsyncGroq(api_key=api_key)
        self.model = settings.GROQ_MODEL

    async def generate_itinerary(self, destination: str, duration_days: int, preferences: str | None = None) -> dict[str, Any]:
        """Generate a full trip itinerary using Groq."""
        user_prompt = f"Plan a {duration_days}-day trip to {destination}."
        if preferences:
            user_prompt += f" The user prefers: {preferences}."
            
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from Groq")
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error generating itinerary: {e}")
            raise
            
    async def regenerate_day(self, destination: str, day_no: int, current_theme: str, preferences: str | None = None) -> dict[str, Any]:
        """Regenerate a single day plan."""
        system_prompt = """You are an expert AI Travel Concierge. Output ONLY valid JSON matching this schema:
{
  "theme": "New theme",
  "description": "New description",
  "activities": [
    {
      "activity": "Brief activity title",
      "scheduled_time": "14:00:00",
      "notes": "Extra details",
      "location": "Place Name"
    }
  ]
}
"""
        user_prompt = f"Regenerate day {day_no} in {destination}. The previous theme was '{current_theme}'."
        if preferences:
            user_prompt += f" Incorporate these preferences: {preferences}."
            
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from Groq")
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error regenerating day plan: {e}")
            raise
