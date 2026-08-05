"""
app/modules/trips/models.py

SQLAlchemy ORM models for Trip, ItineraryItem, and Booking entities.

Technologies: SQLAlchemy 2.x, PostgreSQL, UUID primary keys.

Architecture:
    - Trip is the core planning aggregate owned by a User.
    - ItineraryItem represents a single activity on a specific day of the trip.
    - Booking tracks flights, hotels, and activities linked to a trip.
    - All three use soft-delete to preserve history.

Data Model:
    User        (1) ──< Trip (many)
    Destination (1) ──< Trip (many)   [NEW: Trip now has a destination FK]
    Trip        (1) ──< ItineraryItem (many)
    Trip        (1) ──< Booking (many)

Relationships use lazy="raise" (required for async SQLAlchemy).
"""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, SoftDeleteMixin
from app.modules.trips.enums import BookingStatus, BookingType, TripStatus

__all__ = ["Trip", "ItineraryItem", "Booking"]


class Trip(Base, TimestampMixin, SoftDeleteMixin):
    """
    A user's travel plan — the central aggregate for trip management.

    DB Constraints:
        - CheckConstraint: start_date <= end_date (logically invalid if end before start).
        - user_id FK CASCADE DELETE: deleting a user removes all their trips.
        - destination_id FK SET NULL: deleting a destination does NOT cascade to trips
          (the trip record is preserved even if the destination is removed from catalog).

    Indexes:
        - idx_trips_user_status: Composite index — most trip queries filter by user + status.
        - idx_trips_dates: Composite index — for calendar/date-range trip queries.
    """

    __tablename__ = "trips"

    __table_args__ = (
        # Prevents logically invalid date ranges at the DB level.
        CheckConstraint(
            "start_date IS NULL OR end_date IS NULL OR start_date <= end_date",
            name="ck_trips_date_range",
        ),
        # Composite index: user_id + status is the most common query pair.
        Index("idx_trips_user_status", "user_id", "status"),
        # Composite index: date-range queries for calendar views.
        Index("idx_trips_dates", "start_date", "end_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Numeric, NOT Float — never use floating-point for currency/budget values.
    budget: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=10, scale=2), nullable=True
    )
    status: Mapped[TripStatus] = mapped_column(
        SAEnum(TripStatus, name="trip_status", create_constraint=True),
        default=TripStatus.PLANNING,
        server_default=TripStatus.PLANNING.value,
        nullable=False,
        index=True,
    )

    # Cloudinary URL for trip cover photo.
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ── Foreign Keys ──────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Destination FK: SET NULL on delete — trips are preserved even if the
    # destination is removed from the catalog (historical data integrity).
    destination_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("destinations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Relationships ──────────────────────────────────────
    user: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="trips", lazy="raise"
    )
    destination: Mapped["Destination | None"] = relationship(  # noqa: F821
        "Destination", lazy="raise"
    )
    itinerary_items: Mapped[list["ItineraryItem"]] = relationship(
        "ItineraryItem",
        back_populates="trip",
        cascade="all, delete-orphan",
        lazy="raise",
        passive_deletes=True,
        order_by="ItineraryItem.day_no, ItineraryItem.scheduled_time",
    )
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking",
        back_populates="trip",
        cascade="all, delete-orphan",
        lazy="raise",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Trip id={self.id} title={self.title} status={self.status.value}>"


class ItineraryItem(Base, TimestampMixin, SoftDeleteMixin):
    """
    A single planned activity on a specific day of a trip.

    Example: Day 1, 09:00 — "Visit Eiffel Tower, Paris"

    DB Constraints:
        - CheckConstraint: day_no >= 1 (day 0 is invalid).
        - scheduled_time: PostgreSQL TIME type (not String) for correct sorting.

    Indexes:
        - idx_itinerary_trip_day: Composite index — always fetch items by trip + day.
    """

    __tablename__ = "itinerary_items"

    __table_args__ = (
        CheckConstraint("day_no >= 1", name="ck_itinerary_day_no_positive"),
        Index("idx_itinerary_trip_day", "trip_id", "day_no"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Day number within the trip (1-indexed, not 0-indexed).
    day_no: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    activity: Mapped[str] = mapped_column(String(300), nullable=False)

    # PostgreSQL TIME type: correct sorting, comparison, and display.
    # Previously stored as String(10) which broke time ordering.
    scheduled_time: Mapped[str | None] = mapped_column(Time, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(300), nullable=True)

    # ── Foreign Keys ──────────────────────────────────────
    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Relationships ──────────────────────────────────────
    trip: Mapped["Trip"] = relationship(
        "Trip", back_populates="itinerary_items", lazy="raise"
    )

    def __repr__(self) -> str:
        return (
            f"<ItineraryItem id={self.id} day={self.day_no} "
            f"time={self.scheduled_time} activity={self.activity}>"
        )


class Booking(Base, TimestampMixin, SoftDeleteMixin):
    """
    A booking (flight, hotel, activity) linked to a trip.

    DB Constraints:
        - CheckConstraint: cost >= 0 (negative booking costs are invalid).
        - booking_type: DB-level enum constraint.

    Indexes:
        - idx_bookings_trip_status: Composite index — fetch bookings by trip + status.
        - trip_id: FK index.
    """

    __tablename__ = "bookings"

    __table_args__ = (
        CheckConstraint("cost IS NULL OR cost >= 0", name="ck_bookings_cost_positive"),
        Index("idx_bookings_trip_status", "trip_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    booking_type: Mapped[BookingType] = mapped_column(
        SAEnum(BookingType, name="booking_type", create_constraint=True),
        nullable=False,
    )
    provider: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )  # e.g. "Emirates", "Marriott"

    # Numeric, NOT Float — booking costs are financial values.
    cost: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=10, scale=2), nullable=True
    )
    status: Mapped[BookingStatus] = mapped_column(
        SAEnum(BookingStatus, name="booking_status", create_constraint=True),
        default=BookingStatus.PENDING,
        server_default=BookingStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    confirmation_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # When the booking was made — important for audit trail and booking history.
    booked_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    # ── Foreign Keys ──────────────────────────────────────
    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Relationships ──────────────────────────────────────
    trip: Mapped["Trip"] = relationship(
        "Trip", back_populates="bookings", lazy="raise"
    )

    def __repr__(self) -> str:
        return (
            f"<Booking id={self.id} type={self.booking_type.value} "
            f"status={self.status.value} cost={self.cost}>"
        )
