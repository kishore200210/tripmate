"""
app/modules/destinations/router.py

HTTP Routing Layer — Destinations Module.

Responsibility:
    - Read-only endpoints are public (no auth required).
    - Write endpoints (admin only) require ADMIN role JWT.
    - Prefixed /api/v1/destinations.

MVC Role: Routing Layer.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/destinations", tags=["Destinations"])

# Routes will be implemented in Milestone 2.
