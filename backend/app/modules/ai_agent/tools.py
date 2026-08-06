"""
app/modules/ai_agent/tools.py

LangChain tools for the AI Agent (Weather and Currency).
"""

import json
import logging
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def get_weather_tool(location: str, date: Optional[str] = None) -> str:
    """
    Fetches the current or forecasted weather for a specific location.
    
    Args:
        location: The city and country (e.g., "Paris, France" or "Tokyo, Japan").
        date: The target date (optional, defaults to today).
    """
    logger.info(f"Executing get_weather_tool for location={location}, date={date}")
    
    # Mocking a JSON response for the purpose of this implementation
    # A robust agent will parse this JSON internally.
    try:
        # Simulate network or processing logic here
        result = {
            "location": location,
            "temperature_celsius": 24,
            "condition": "Sunny with light clouds",
            "humidity": "45%",
            "wind_speed": "12 km/h"
        }
        return json.dumps(result)
    except Exception as e:
        logger.error(f"Weather tool failed: {e}")
        return json.dumps({"error": "Failed to fetch weather data."})


@tool
def get_currency_tool(base_currency: str, target_currency: str, amount: float) -> str:
    """
    Fetches the exchange rate and calculates the converted amount.
    
    Args:
        base_currency: The 3-letter currency code to convert from (e.g., "USD").
        target_currency: The 3-letter currency code to convert to (e.g., "EUR").
        amount: The amount of base_currency to convert.
    """
    logger.info(f"Executing get_currency_tool: {amount} {base_currency} to {target_currency}")
    
    # Mocking exchange rates
    mock_rates = {
        "USD_TO_EUR": 0.92,
        "EUR_TO_USD": 1.08,
        "USD_TO_JPY": 150.25,
        "JPY_TO_USD": 0.0067,
    }
    
    key = f"{base_currency.upper()}_TO_{target_currency.upper()}"
    
    try:
        rate = mock_rates.get(key, 1.0) # Default 1.0 for unmocked pairs
        converted = amount * rate
        
        result = {
            "base": base_currency.upper(),
            "target": target_currency.upper(),
            "original_amount": amount,
            "converted_amount": round(converted, 2),
            "exchange_rate": rate
        }
        return json.dumps(result)
    except Exception as e:
        logger.error(f"Currency tool failed: {e}")
        return json.dumps({"error": "Failed to fetch currency data."})
