"""
app/core/router.py

System-level router for infrastructure endpoints.

Responsibility:
    - Hosts the /health endpoint for load balancer and monitoring checks.
    - Registered in main.py under no prefix (root level).

MVC Role: Routing Layer — extracted from the application factory to enforce SRP.
         Health check is a route, not application configuration logic.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
import redis.asyncio as redis
from app.core.config import get_settings

router = APIRouter(tags=["System"])
settings = get_settings()


@router.get("/health", response_class=JSONResponse)
async def health_check() -> dict:
    """
    Public health check endpoint.

    Used by:
        - Docker HEALTHCHECK instruction.
        - Render / Railway health probe.
        - Load balancer readiness checks.

    Returns HTTP 200 when the application is running normally.
    """
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }

@router.get("/health/db", tags=["System"], summary="Deep Health Check")
async def db_health_check(db: Session = Depends(get_db)):
    """Deep health check that verifies PostgreSQL and Redis connectivity."""
    components = {"postgres": "down", "redis": "down"}
    is_healthy = True

    try:
        db.execute(text("SELECT 1"))
        components["postgres"] = "up"
    except Exception:
        is_healthy = False

    try:
        r = redis.from_url(settings.REDIS_URL)
        await r.ping()
        components["redis"] = "up"
        await r.aclose()
    except Exception:
        is_healthy = False

    status_code = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ok" if is_healthy else "error",
            "components": components
        }
    )
