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
    - Post-processes results with relevance scoring, deduplication,
      and place-type resolution optimised for travel destination search.

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


# ── Maximum results returned to the frontend ───────────────────────────────────

_MAX_RESULTS = 8

# ── Irrelevant Nominatim classes for travel destination search ─────────────────
# These are filtered out entirely — they are never useful destinations.

_IRRELEVANT_CLASSES: set[str] = {
    "shop", "amenity", "building", "office", "craft", "man_made",
    "club", "healthcare", "industrial", "landuse", "power",
}

# ── Irrelevant (class, type) pairs ─────────────────────────────────────────────
# Specific combinations that shouldn't appear even if the class is allowed.

_IRRELEVANT_PAIRS: set[tuple[str, str]] = {
    ("highway", "residential"),
    ("highway", "service"),
    ("highway", "tertiary"),
    ("highway", "secondary"),
    ("highway", "unclassified"),
    ("highway", "track"),
    ("highway", "footway"),
    ("highway", "path"),
    ("highway", "cycleway"),
    ("highway", "bus_stop"),
    ("highway", "crossing"),
    ("railway", "halt"),
    ("railway", "tram_stop"),
}

# ── Relevance scoring by (class, type) and addresstype ─────────────────────────
# Higher score = more relevant as a travel destination.

_TYPE_SCORES: dict[str, int] = {
    # addresstype-based (most reliable for admin boundaries)
    "country": 100,
    "state": 90,
    "province": 90,
    "region": 85,
    "county": 70,
    "city": 80,
    "town": 75,
    "village": 65,
    "hamlet": 55,
    "suburb": 40,
    "quarter": 35,
    "neighbourhood": 30,
    "municipality": 75,
    "district": 60,
    "borough": 50,
    # Nominatim type-based
    "island": 85,
    "archipelago": 85,
    "continent": 100,
    "administrative": 70,  # generic fallback for boundaries
}

# ── Place type resolution ──────────────────────────────────────────────────────
# Uses addresstype (most accurate) → type → class to derive a human label.

_ADDRESSTYPE_LABELS: dict[str, str] = {
    "country": "Country",
    "state": "State/Province",
    "province": "State/Province",
    "region": "Region",
    "county": "County",
    "city": "City",
    "town": "Town",
    "village": "Village",
    "hamlet": "Hamlet",
    "suburb": "Suburb",
    "quarter": "District",
    "neighbourhood": "Neighbourhood",
    "municipality": "Municipality",
    "district": "District",
    "borough": "Borough",
    "island": "Island",
    "archipelago": "Archipelago",
    "continent": "Continent",
}

_TYPE_LABELS: dict[str, str] = {
    "city": "City",
    "town": "Town",
    "village": "Village",
    "country": "Country",
    "state": "State/Province",
    "county": "County",
    "suburb": "Suburb",
    "quarter": "District",
    "municipality": "Municipality",
    "island": "Island",
    "archipelago": "Archipelago",
    "peak": "Mountain Peak",
    "volcano": "Volcano",
    "beach": "Beach",
    "cape": "Cape",
    "bay": "Bay",
    "glacier": "Glacier",
    "desert": "Desert",
    "national_park": "National Park",
    "nature_reserve": "Nature Reserve",
    "protected_area": "Protected Area",
}

_CLASS_LABELS: dict[str, str] = {
    "tourism": "Tourist Attraction",
    "natural": "Natural Feature",
    "leisure": "Leisure",
    "historic": "Historic Site",
    "aeroway": "Airport",
    "waterway": "Waterway",
}


# ── Nominatim normaliser ───────────────────────────────────────────────────────

def _resolve_place_type(raw: dict[str, Any]) -> str | None:
    """Derive a human-readable place type label from Nominatim fields.

    Priority: addresstype → type → class → fallback.
    """
    addresstype = (raw.get("addresstype") or "").lower()
    osm_type = (raw.get("type") or "").lower()
    osm_class = (raw.get("class") or "").lower()

    # 1. addresstype is the most reliable for admin boundaries
    if addresstype in _ADDRESSTYPE_LABELS:
        return _ADDRESSTYPE_LABELS[addresstype]

    # 2. Nominatim type field
    if osm_type in _TYPE_LABELS:
        return _TYPE_LABELS[osm_type]

    # 3. Class-level fallback
    if osm_class in _CLASS_LABELS:
        return _CLASS_LABELS[osm_class]

    # 4. Capitalise the type as a last resort
    if osm_type:
        return osm_type.replace("_", " ").capitalize()

    return None


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

    place_type = _resolve_place_type(raw)

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


# ── Relevance scoring ─────────────────────────────────────────────────────────

def _relevance_score(raw: dict[str, Any], query_lower: str) -> float:
    """Compute a relevance score for a raw Nominatim result.

    Higher score = more relevant as a travel destination.
    Components:
        - Base score from addresstype/type (0–100)
        - Nominatim importance bonus (0–60) — heavily weighted so globally
          significant places (London UK > London Canada) rank higher
        - Name match bonus: exact (50) or partial/contains (25)
    """
    addresstype = (raw.get("addresstype") or "").lower()
    osm_type = (raw.get("type") or "").lower()

    # Base score from the type hierarchy
    base = (
        _TYPE_SCORES.get(addresstype)
        or _TYPE_SCORES.get(osm_type)
        or 20  # unknown type gets a low base
    )

    # Nominatim importance (0.0–1.0) — higher for more globally significant places
    # Scaled to 0–60 so that e.g. London UK (importance ≈ 0.85) gets ~51
    # while London Canada (importance ≈ 0.45) gets ~27
    importance = float(raw.get("importance", 0.0))
    importance_bonus = importance * 60

    # Name match bonus — exact match is best, contains is next.
    # The gap is kept small (40 vs 30) so that Nominatim's global importance
    # signal dominates for well-known namesakes (e.g. London UK > London Canada).
    raw_name = (raw.get("name") or "").lower()
    display_name_lower = (raw.get("display_name") or "").lower()
    if raw_name == query_lower:
        name_bonus = 40  # exact match (e.g. "london" == "london")
    elif query_lower in raw_name or query_lower in display_name_lower:
        name_bonus = 30  # partial match (e.g. "Greater London" contains "london")
    else:
        name_bonus = 0

    return base + importance_bonus + name_bonus


def _is_relevant(raw: dict[str, Any], query_lower: str) -> bool:
    """Return True if this Nominatim result is relevant for travel search.

    Checks:
        1. Class/type is not in the irrelevant blocklist
        2. The result name or display_name contains the query term
           (prevents e.g. 'Paris' appearing in a 'Bali' search)
    """
    osm_class = (raw.get("class") or "").lower()
    osm_type = (raw.get("type") or "").lower()

    # Filter out entirely irrelevant classes
    if osm_class in _IRRELEVANT_CLASSES:
        return False

    # Filter out specific irrelevant (class, type) pairs
    if (osm_class, osm_type) in _IRRELEVANT_PAIRS:
        return False

    # Filter out results whose name/display_name doesn't contain the query.
    # This prevents Nominatim's fuzzy matching from returning completely
    # unrelated places (e.g. "Bad Liebenwerda" or "Paris" for query "Bali").
    raw_name = (raw.get("name") or "").lower()
    display_name = (raw.get("display_name") or "").lower()
    if query_lower not in raw_name and query_lower not in display_name:
        return False

    return True


# ── Deduplication ──────────────────────────────────────────────────────────────

def _deduplicate(
    scored_results: list[tuple[float, dict[str, Any]]],
) -> list[tuple[float, dict[str, Any]]]:
    """Remove near-duplicate results, keeping the highest-scored entry per group.

    Duplicates are identified by (normalised_name, country_code).
    This eliminates e.g. three "Paris, France" entries with slightly
    different coordinates while preserving "Paris, France" vs "Paris, Texas".
    """
    seen: dict[tuple[str, str], tuple[float, dict[str, Any]]] = {}

    for score, raw in scored_results:
        name = (raw.get("name") or "").strip().lower()
        addr = raw.get("address", {})
        cc = (addr.get("country_code") or "").lower()
        state = (addr.get("state") or "").strip().lower()

        # Key: (name, country_code, state) — preserves city vs state distinction
        # e.g. "New York" city vs "New York" state
        dedup_key = (name, cc, state)

        existing = seen.get(dedup_key)
        if existing is None or score > existing[0]:
            seen[dedup_key] = (score, raw)

    return list(seen.values())


# ── Rank, filter, deduplicate pipeline ─────────────────────────────────────────

def _rank_and_filter(
    raw_results: list[dict[str, Any]], query: str,
) -> list[PlaceResult]:
    """Process raw Nominatim results into ranked, filtered, deduplicated places.

    Pipeline:
        1. Filter out irrelevant classes/types
        2. Score each result for travel relevance
        3. Deduplicate by (name, country_code, state)
        4. Sort by score descending
        5. Normalise to PlaceResult
        6. Cap at _MAX_RESULTS
    """
    query_lower = query.strip().lower()

    # Step 1 + 2: filter and score
    scored: list[tuple[float, dict[str, Any]]] = []
    for raw in raw_results:
        if not _is_relevant(raw, query_lower):
            logger.debug(
                "Filtered out irrelevant result: %s (class=%s, type=%s)",
                raw.get("display_name", "?"),
                raw.get("class", "?"),
                raw.get("type", "?"),
            )
            continue
        score = _relevance_score(raw, query_lower)
        scored.append((score, raw))

    # Step 3: deduplicate
    deduped = _deduplicate(scored)

    # Step 4: sort by score descending
    deduped.sort(key=lambda x: x[0], reverse=True)

    # Step 5 + 6: normalise and cap
    results = [_normalise(raw) for _, raw in deduped[:_MAX_RESULTS]]

    return results


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
                    "limit": "20",       # Fetch more for post-filtering
                    "dedupe": "1",
                    "layer": "address",  # Restrict to address layer (countries,
                                         # states, cities, towns, villages) —
                                         # excludes POIs, shops, buildings, etc.
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

    # Rank, filter, deduplicate, and normalise results
    results = _rank_and_filter(raw_results, q)

    # Cache serialised dicts (Pydantic models are not directly cacheable)
    _cache_set(cache_key, [r.model_dump() for r in results])

    return results
