"""
app/db/model_registry.py

Central model import registry for Alembic autogenerate.

IMPORTANT:
    Every SQLAlchemy model MUST be imported here so that Alembic's
    autogenerate feature can detect the full schema when generating migrations.

    If you add a new model, import it here. Failure to do so will result
    in Alembic not generating migration steps for that table.

Architecture:
    - This module is imported in alembic/env.py before calling Base.metadata.
    - It does NOT contain any logic — only imports.
"""

# ── DO NOT REMOVE — Required for Alembic autogenerate ─────

from app.db.base import Base  # noqa: F401 — exposes Base.metadata

# Users
from app.modules.users.models import User  # noqa: F401

# Destinations, Reviews, Documents
from app.modules.destinations.models import (  # noqa: F401
    Destination,
    Review,
    Document,
)

# Trips, ItineraryItems, Bookings, Itinerary, DayPlan
from app.modules.trips.models import (  # noqa: F401
    Trip,
    ItineraryItem,
    Booking,
    Itinerary,
    DayPlan,
)

# AI Concierge
from app.modules.ai_concierge.models import ChatMessage  # noqa: F401

# When new models are added in future milestones, import them below:
# from app.modules.analytics.models import AnalyticsSnapshot  # noqa: F401
