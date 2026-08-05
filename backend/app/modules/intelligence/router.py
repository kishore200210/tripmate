"""
app/modules/intelligence/router.py

HTTP Routing Layer — Intelligence Module (ML + CV).

Responsibility:
    - Endpoint for landmark detection (Computer Vision).
    - Endpoint for destination recommendations (ML model).
    - Prefixed /api/v1/intelligence.

MVC Role: Routing Layer.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/intelligence", tags=["Intelligence"])

# Routes will be implemented in Milestone 8 (ML + CV).
