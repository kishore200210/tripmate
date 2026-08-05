"""
app/modules/trips/models.py

SQLAlchemy ORM models for Trip, ItineraryItem, and Booking entities.

Technologies: SQLAlchemy, PostgreSQL, UUID primary keys.

Architecture:
    - Trip is the core planning aggregate owned by a User.
    - ItineraryItem represents a single activity on a specific day of the trip.
    - Booking tracks flights, hotels, and activities linked to a trip.
    - All three use soft-delete to preserve history.

Data Model:
    Trip belongs to User
    Trip has many ItineraryItems
    Trip has many Bookings
"""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Date,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.base import Base, TimestampMixin, SoftDeleteMixin


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


class Trip(Base, TimestampMixin, SoftDeleteMixin):
    """
    A user's travel plan — the central aggregate for trip management.

    Indexes:
        - user_id: For fetching all trips belonging to a user.
        - status: For filtering active/completed trips.
    """

    __tablename__ = "trips"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    budget: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=10, scale=2), nullable=True
    )
    status: Mapped[TripStatus] = mapped_column(
        SAEnum(TripStatus, name="trip_status"),
        default=TripStatus.PLANNING,
        nullable=False,
        index=True,
    )
    # Cloudinary image URL for trip cover photo
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ── Foreign Keys ───────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Relationships ───────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="trips")  # noqa: F821
    itinerary_items: Mapped[list["ItineraryItem"]] = relationship(
        "ItineraryItem", back_populates="trip", cascade="all, delete-orphan"
    )
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking", back_populates="trip", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Trip id={self.id} title={self.title} status={self.status}>"


class ItineraryItem(Base, TimestampMixin, SoftDeleteMixin):
    """
    A single planned activity on a specific day of a trip.

    Example: Day 1, 09:00 AM — "Visit Eiffel Tower"

    Indexes:
        - trip_id: For fetching all items for a specific trip.
        - day_no: For ordering items within a trip's timeline.
    """

    __tablename__ = "itinerary_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    day_no: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    activity: Mapped[str] = mapped_column(String(300), nullable=False)
    scheduled_time: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )  # e.g. "09:00"
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(300), nullable=True)

    # ── Foreign Keys ───────────────────────────────────────
    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Relationships ───────────────────────────────────────
    trip: Mapped["Trip"] = relationship("Trip", back_populates="itinerary_items")

    def __repr__(self) -> str:
        return f"<ItineraryItem id={self.id} day={self.day_no} activity={self.activity}>"


class Booking(Base, TimestampMixin, SoftDeleteMixin):
    """
    A booking (flight, hotel, activity) linked to a trip.

    Indexes:
        - trip_id: For fetching all bookings for a trip.
        - status: For filtering confirmed vs cancelled bookings.
    """

    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    booking_type: Mapped[BookingType] = mapped_column(
        SAEnum(BookingType, name="booking_type"), nullable=False
    )
    provider: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )  # e.g. "Emirates", "Marriott"
    cost: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=10, scale=2), nullable=True
    )
    status: Mapped[BookingStatus] = mapped_column(
        SAEnum(BookingStatus, name="booking_status"),
        default=BookingStatus.PENDING,
        nullable=False,
        index=True,
    )
    confirmation_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Foreign Keys ───────────────────────────────────────
    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Relationships ───────────────────────────────────────
    trip: Mapped["Trip"] = relationship("Trip", back_populates="bookings")

    def __repr__(self) -> str:
        return f"<Booking id={self.id} type={self.booking_type} status={self.status}>"
