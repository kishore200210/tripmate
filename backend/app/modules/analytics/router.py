"""
app/modules/analytics/router.py

HTTP Routing Layer — Analytics Module.

Responsibility:
    - Endpoints for admin analytics dashboard (trip counts, popular destinations).
    - All endpoints require ADMIN role.
    - Prefixed /api/v1/analytics.

MVC Role: Routing Layer.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Routes will be implemented in Milestone 8 (Analytics).
