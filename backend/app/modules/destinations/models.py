"""
app/modules/destinations/models.py

SQLAlchemy ORM models for Destination, Review, and Document entities.

Technologies: SQLAlchemy 2.x, pgvector, PostgreSQL.

Architecture:
    - Destination is the core catalog entity — places users plan trips to.
    - Review bridges User and Destination (many-to-many with payload).
    - Document stores chunked travel guide text + pgvector embedding for RAG.

Data Model:
    Destination (1) ──< Review (many)
    Destination (1) ──< Document (many)
    User        (1) ──< Review (many)

Relationships use lazy="raise" (required for async SQLAlchemy).
"""

import uuid
from decimal import Decimal

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin

# OpenAI text-embedding-3-small produces 1536-dimensional vectors.
# If the embedding model changes, update this constant AND run a migration.
EMBEDDING_DIMENSIONS = 1536

__all__ = ["Destination", "Review", "Document"]


class Destination(Base, TimestampMixin, SoftDeleteMixin):
    """
    Travel destination catalog entry.

    DB Constraints:
        - name: NOT NULL, indexed for text search.
        - country: NOT NULL, indexed for geographic filtering.
        - avg_budget: Numeric(10,2) — never Float for financial values.

    Indexes:
        - idx_destinations_country_name: Composite index for country+name searches.
        - is_deleted: From SoftDeleteMixin — always filter active destinations.
    """

    __tablename__ = "destinations"

    __table_args__ = (
        # Composite index: most destination queries filter by country, then name.
        Index("idx_destinations_country_name", "country", "name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Type annotation corrected: nullable=True means Python type must be str | None
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ARRAY(String): PostgreSQL native array for tags used by ML recommender.
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    # Specific city within the country (e.g., "Kyoto" within "Japan").
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Human-readable travel season, e.g. "March–May" or "Year-round".
    best_time_to_visit: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Recommended trip length in days.
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Cloudinary URL for the destination hero image.
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Numeric, NOT Float — financial values must never use floating-point types.
    avg_budget: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=10, scale=2), nullable=True
    )

    # pgvector column — 1536-dim vector for semantic destination search
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIMENSIONS), nullable=True
    )


    # ── Relationships ──────────────────────────────────────
    reviews: Mapped[list["Review"]] = relationship(
        "Review",
        back_populates="destination",
        cascade="all, delete-orphan",
        lazy="raise",
        passive_deletes=True,
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="destination",
        cascade="all, delete-orphan",
        lazy="raise",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Destination id={self.id} name={self.name} country={self.country}>"


class Review(Base, TimestampMixin, SoftDeleteMixin):
    """
    User review for a specific destination.

    DB Constraints:
        - UniqueConstraint(user_id, destination_id): One review per user per destination.
          Enforced at DB level — service layer alone is NOT sufficient for uniqueness.
        - CheckConstraint(rating BETWEEN 1 AND 5): Invalid ratings rejected by DB.
          This is a data integrity guarantee, not just a validation rule.

    Indexes:
        - idx_reviews_destination_rating: Composite index for avg rating queries.
        - user_id: FK index for fetching all reviews by a user.
    """

    __tablename__ = "reviews"

    __table_args__ = (
        # DB-level uniqueness: one review per user per destination.
        # Service-layer validation alone is insufficient (race conditions).
        UniqueConstraint("user_id", "destination_id", name="uq_reviews_user_destination"),
        # DB-level rating range constraint: rating must be 1–5.
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating_range"),
        # Composite index for destination rating aggregation queries.
        Index("idx_reviews_destination_rating", "destination_id", "rating"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # SmallInteger is correct for a 1–5 rating — saves storage vs Integer.
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Foreign Keys ──────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    destination_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("destinations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Relationships ──────────────────────────────────────
    user: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="reviews", lazy="raise"
    )
    destination: Mapped["Destination"] = relationship(
        "Destination", back_populates="reviews", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<Review id={self.id} rating={self.rating} destination={self.destination_id}>"


class Document(Base, TimestampMixin):
    """
    A chunked travel guide document used for RAG (Retrieval-Augmented Generation).

    Architecture:
        - A single source file is split into chunks at the Service layer.
        - Each chunk is stored as a separate Document row.
        - chunk_index preserves the original order of chunks from the same source.
        - source_file records which file the chunk came from (for RAG citations).
        - embedding stores the pgvector 1536-dim vector for cosine similarity search.

    DB Constraints:
        - UniqueConstraint(destination_id, source_file, chunk_index):
          Prevents duplicate chunk ingestion (idempotent RAG pipeline).

    Indexes:
        - destination_id: FK index for fetching all documents for a destination.
        - Note: pgvector index (HNSW or IVFFlat) must be added via a raw migration
          on the embedding column for production performance. Alembic autogenerate
          does not support pgvector index creation natively.
    """

    __tablename__ = "documents"

    __table_args__ = (
        # Prevents re-ingesting the same chunk from the same source file.
        UniqueConstraint(
            "destination_id", "source_file", "chunk_index",
            name="uq_documents_destination_source_chunk"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)

    # The raw text content of this chunk.
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Source file path or name — used for RAG answer citations.
    # e.g. "bali_travel_guide_2025.md" or "paris_official_guide.pdf"
    source_file: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Position of this chunk within its source file.
    # Required to reconstruct document order for multi-chunk context windows.
    chunk_index: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    # pgvector column — 1536-dim vector from OpenAI text-embedding-3-small.
    # Nullable until the embedding job has processed this chunk.
    # Production: add HNSW index via manual migration for fast ANN search.
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIMENSIONS), nullable=True
    )

    # ── Foreign Keys ──────────────────────────────────────
    destination_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("destinations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Relationships ──────────────────────────────────────
    destination: Mapped["Destination"] = relationship(
        "Destination", back_populates="documents", lazy="raise"
    )

    def __repr__(self) -> str:
        return (
            f"<Document id={self.id} source={self.source_file} "
            f"chunk={self.chunk_index} destination={self.destination_id}>"
        )
