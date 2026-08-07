"""
app/modules/places/router.py

Places Search API — proxies OpenStreetMap Nominatim geocoding.

Architecture:
    - Exposes GET /places/search?q=<query>
    - Proxies to Nominatim (free, no API key required).
    - Caches responses in-memory (128 entries, 5-minute TTL) to respect
      Nominatim's 1 req/second rate limit and improve latency.
    - Requires 2+ character queries to avoid over-fetching.
    - Uses httpx.AsyncClient for non-blocking HTTP.

Nominatim policy: https://operations.osmfoundation.org/policies/nominatim/
    - Must send meaningful User-Agent.
    - Max 1 request per second.
    - Must NOT send bulk or automated queries.
"""

import logging
import time
from typing import Any

import httpx
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/places",
    tags=["Places"],
)

# ── In-memory Cache ────────────────────────────────────────────────────────────
# Simple dict-based TTL cache — avoids a Redis dependency for this use case.

_CACHE_TTL_SECONDS = 300  # 5 minutes
_MAX_CACHE_ENTRIES = 128

_cache: dict[str, tuple[float, list[dict]]] = {}  # key → (timestamp, results)


def _cache_get(key: str) -> list[dict] | None:
    """Return cached result if still fresh, else None."""
    entry = _cache.get(key)
    if entry is None:
        return None
    ts, data = entry
    if time.monotonic() - ts > _CACHE_TTL_SECONDS:
        del _cache[key]
        return None
    return data


def _cache_set(key: str, data: list[dict]) -> None:
    """Store result. Evicts oldest entries when at capacity."""
    if len(_cache) >= _MAX_CACHE_ENTRIES:
        # Evict the single oldest entry to keep memory bounded.
        oldest_key = min(_cache, key=lambda k: _cache[k][0])
        del _cache[oldest_key]
    _cache[key] = (time.monotonic(), data)


# ── Response Schema ────────────────────────────────────────────────────────────

class PlaceResult(BaseModel):
    """Normalised geocoding result returned to the frontend."""
    place_id: str
    display_name: str
    name: str
    city: str | None
    state: str | None
    country: str | None
    country_code: str | None   # ISO 3166-1 alpha-2, e.g. "in", "de"
    place_type: str | None     # e.g. "city", "country", "village"
    latitude: float | None
    longitude: float | None


# ── Nominatim normaliser ───────────────────────────────────────────────────────

def _normalise(raw: dict[str, Any]) -> PlaceResult:
    """Map a raw Nominatim JSON object → PlaceResult."""
    addr: dict = raw.get("address", {})

    # Resolve the human-readable name (prefer city > town > village > county)
    name = (
        raw.get("name")
        or addr.get("city")
        or addr.get("town")
        or addr.get("village")
        or addr.get("county")
        or raw.get("display_name", "").split(",")[0].strip()
    )

    city = (
        addr.get("city")
        or addr.get("town")
        or addr.get("village")
        or addr.get("municipality")
    )

    # Nominatim returns a class+type pair — map to readable place_type
    osm_type = raw.get("type", raw.get("class", ""))
    type_map = {
        "city": "City",
        "town": "Town",
        "village": "Village",
        "administrative": "Region",
        "country": "Country",
        "state": "State/Province",
        "county": "County",
        "suburb": "Suburb",
        "quarter": "District",
        "municipality": "Municipality",
    }
    place_type = type_map.get(osm_type, osm_type.capitalize() if osm_type else None)

    lat = raw.get("lat")
    lon = raw.get("lon")

    return PlaceResult(
        place_id=str(raw.get("place_id", "")),
        display_name=raw.get("display_name", name),
        name=name,
        city=city,
        state=addr.get("state") or addr.get("region"),
        country=addr.get("country"),
        country_code=addr.get("country_code"),
        place_type=place_type,
        latitude=float(lat) if lat else None,
        longitude=float(lon) if lon else None,
    )


# ── Endpoint ───────────────────────────────────────────────────────────────────

@router.get(
    "/search",
    response_model=list[PlaceResult],
    summary="Search places worldwide via Nominatim geocoding",
    description=(
        "Proxies OpenStreetMap Nominatim. Returns up to 8 place suggestions "
        "for the given query string. Requires at least 2 characters. "
        "Results are cached for 5 minutes."
    ),
)
async def search_places(
    q: str = Query(..., min_length=2, max_length=200, description="Place search query"),
) -> list[PlaceResult]:
    """Search for places using OpenStreetMap Nominatim geocoding."""
    cache_key = q.strip().lower()

    # Return cached result if available
    cached = _cache_get(cache_key)
    if cached is not None:
        logger.debug("places cache hit: %s", cache_key)
        return [PlaceResult(**item) for item in cached]

    logger.debug("places cache miss: %s — fetching from Nominatim", cache_key)

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": q.strip(),
                    "format": "json",
                    "addressdetails": "1",
                    "limit": "8",
                    "dedupe": "1",
                },
                headers={
                    # Required by Nominatim usage policy
                    "User-Agent": "TripMate-Capstone/1.0 (github.com/tripmate-capstone)",
                    "Accept-Language": "en",
                },
            )
            response.raise_for_status()
            raw_results: list[dict] = response.json()

    except httpx.TimeoutException:
        logger.warning("Nominatim request timed out for query: %s", q)
        raise HTTPException(status_code=504, detail="Place search timed out. Please try again.")
    except httpx.HTTPStatusError as exc:
        logger.error("Nominatim HTTP error %s for query: %s", exc.response.status_code, q)
        raise HTTPException(status_code=502, detail="Place search service error.")
    except Exception as exc:
        logger.exception("Unexpected error during place search for query: %s", q)
        raise HTTPException(status_code=500, detail="Place search failed.")

    results = [_normalise(r) for r in raw_results]

    # Cache serialised dicts (Pydantic models are not directly cacheable)
    _cache_set(cache_key, [r.model_dump() for r in results])

    return results
