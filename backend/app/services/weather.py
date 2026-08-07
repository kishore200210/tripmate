"""
app/services/weather.py
"""
import httpx
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

class WeatherService:
    @staticmethod
    async def get_weather(location: str) -> Dict[str, Any]:
        """
        Geocodes the location and fetches weather from Open-Meteo.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 1. Geocoding
                geo_url = "https://geocoding-api.open-meteo.com/v1/search"
                geo_resp = await client.get(geo_url, params={"name": location, "count": 1})
                geo_resp.raise_for_status()
                geo_data = geo_resp.json()
                
                if not geo_data.get("results"):
                    return {"error": f"Could not find coordinates for location: {location}"}
                
                lat = geo_data["results"][0]["latitude"]
                lon = geo_data["results"][0]["longitude"]
                resolved_name = f"{geo_data['results'][0].get('name')}, {geo_data['results'][0].get('country', '')}"

                # 2. Weather
                weather_url = "https://api.open-meteo.com/v1/forecast"
                params = {
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code",
                    "timezone": "auto"
                }
                weather_resp = await client.get(weather_url, params=params)
                weather_resp.raise_for_status()
                w_data = weather_resp.json().get("current", {})

                # Weather codes mapping (simplified)
                w_code = w_data.get("weather_code", 0)
                condition = "Clear"
                if w_code in [1, 2, 3]: condition = "Cloudy"
                elif w_code in [45, 48]: condition = "Fog"
                elif 50 <= w_code <= 69: condition = "Rain"
                elif 70 <= w_code <= 79: condition = "Snow"
                elif w_code >= 80: condition = "Storm/Heavy Rain"

                return {
                    "location": resolved_name,
                    "temperature_celsius": w_data.get("temperature_2m"),
                    "humidity": f"{w_data.get('relative_humidity_2m')}%",
                    "precipitation": f"{w_data.get('precipitation')} mm",
                    "wind_speed": f"{w_data.get('wind_speed_10m')} km/h",
                    "condition": condition
                }
        except Exception as e:
            logger.error(f"WeatherService error: {e}")
            return {"error": "Failed to fetch weather data."}
