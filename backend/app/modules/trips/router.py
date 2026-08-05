"""
app/modules/trips/router.py

HTTP Routing Layer — Trips Module.

Responsibility:
    - Maps HTTP verbs + paths to controller functions ONLY.
    - All routes require JWT authentication (enforced via middleware dependency).
    - Prefixed /api/v1/trips.

MVC Role: Routing Layer.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/trips", tags=["Trips"])

# Routes will be implemented in Milestone 2.
