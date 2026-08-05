"""
app/modules/destinations/models.py

SQLAlchemy ORM models for Destination, Review, and Document entities.

Technologies: SQLAlchemy, pgvector (for Document embeddings), PostgreSQL.

Architecture:
    - Destination is the core catalog entity — the places users plan trips to.
    - Review belongs to both User and Destination (many-to-many bridge).
    - Document stores full travel guide text AND its vector embedding for RAG.
      The 'embedding' column uses pgvector's VECTOR type for similarity search.

Data Model:
    Destination has many Reviews
    Destination has many Documents
    Document has one embedding (pgvector VECTOR) for RAG retrieval
"""

import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin

# Dimension for OpenAI text-embedding-3-small model
EMBEDDING_DIMENSIONS = 1536


class Destination(Base, TimestampMixin, SoftDeleteMixin):
    """
    Travel destination catalog entry.

    Indexes:
        - country: For geographic filtering.
        - name: For text search.

    The 'tags' column stores a list of interest keywords (e.g. ["beach", "family"])
    used by the ML recommendation engine.
    """

    __tablename__ = "destinations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    avg_budget: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Relationships ──────────────────────────────────────
    reviews: Mapped[list["Review"]] = relationship(
        "Review", back_populates="destination", cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="destination", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Destination id={self.id} name={self.name} country={self.country}>"


class Review(Base, TimestampMixin, SoftDeleteMixin):
    """
    User review for a specific destination.

    Constraints:
        - rating is 1–5 integer (enforced at service layer).
        - A user can review a destination only once (enforced at service layer).
    """

    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Foreign Keys ───────────────────────────────────────
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

    # ── Relationships ───────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="reviews")  # noqa: F821
    destination: Mapped["Destination"] = relationship(
        "Destination", back_populates="reviews"
    )

    def __repr__(self) -> str:
        return f"<Review id={self.id} rating={self.rating} destination={self.destination_id}>"


class Document(Base, TimestampMixin):
    """
    Travel guide document for RAG (Retrieval-Augmented Generation).

    The 'embedding' column stores the OpenAI text-embedding-3-small vector
    (1536 dimensions) using pgvector. This is queried via cosine similarity
    during RAG retrieval to find relevant context for the LLM.

    Architecture Note:
        - Documents are chunked at the Service layer before embedding.
        - Each chunk is stored as a separate Document row.
        - The RAG service queries this table using pgvector's <=> operator.
    """

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # pgvector column — stores the 1536-dimensional embedding vector
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIMENSIONS), nullable=True
    )

    # ── Foreign Keys ───────────────────────────────────────
    destination_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("destinations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Relationships ───────────────────────────────────────
    destination: Mapped["Destination"] = relationship(
        "Destination", back_populates="documents"
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} title={self.title} destination={self.destination_id}>"
