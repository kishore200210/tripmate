"""
app/services/currency.py
"""
import httpx
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

class CurrencyService:
    @staticmethod
    async def convert(base_currency: str, target_currency: str, amount: float) -> Dict[str, Any]:
        """
        Fetches live exchange rates and converts the amount.
        """
        base = base_currency.upper()
        target = target_currency.upper()
        
        try:
            url = f"https://open.er-api.com/v6/latest/{base}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                
                rates = data.get("rates", {})
                if target not in rates:
                    return {"error": f"Unsupported target currency: {target}"}
                
                rate = rates[target]
                converted = amount * rate
                
                return {
                    "base": base,
                    "target": target,
                    "original_amount": amount,
                    "converted_amount": round(converted, 2),
                    "exchange_rate": rate
                }
        except Exception as e:
            logger.error(f"CurrencyService error: {e}")
            return {"error": "Failed to fetch currency data."}
