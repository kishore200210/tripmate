"""
app/core/router.py

System-level router for infrastructure endpoints.

Responsibility:
    - Hosts the /health endpoint for load balancer and monitoring checks.
    - Registered in main.py under no prefix (root level).

MVC Role: Routing Layer — extracted from the application factory to enforce SRP.
         Health check is a route, not application configuration logic.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

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
    Does NOT check database connectivity (use /health/db for that in future).
    """
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }
