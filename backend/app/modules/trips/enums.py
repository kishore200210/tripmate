"""
app/modules/trips/enums.py

Domain enums for the Trips module.

Why separate from models.py:
    - Needed by models.py, schemas.py, and service.py.
    - Prevents circular imports between layers.
"""

import enum


class TripStatus(str, enum.Enum):
    """Lifecycle status of a trip."""

    PLANNING = "planning"
    CONFIRMED = "confirmed"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BookingType(str, enum.Enum):
    """Type of booking attached to a trip."""

    FLIGHT = "flight"
    HOTEL = "hotel"
    ACTIVITY = "activity"
    TRANSPORT = "transport"
    OTHER = "other"


class BookingStatus(str, enum.Enum):
    """Confirmation status of a booking."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
