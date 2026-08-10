"""
app/modules/destinations/service.py

Destination Service — all business logic for destination management.

Responsibilities:
    - Input validation beyond schema-level rules (e.g. uniqueness checks).
    - Orchestrating repository calls.
    - Mapping domain models to/from Pydantic response schemas.
    - Image file handling for local uploads.

Architecture:
    - Zero HTTP knowledge here — raises domain exceptions only.
    - Controllers call services; services call repositories.
"""

import logging
import shutil
import uuid
from pathlib import Path
from uuid import UUID
from typing import Any

from fastapi import UploadFile

from app.core.embeddings import EmbeddingService
from app.core.exceptions import (
    BusinessRuleViolationException,
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
    ValidationException,
)
from app.modules.destinations.models import Destination
from app.modules.destinations.repository import DestinationRepository
from app.modules.destinations.schemas import (
    DestinationCountResponse,
    DestinationCreateRequest,
    DestinationPaginatedResponse,
    DestinationResponse,
    DestinationUpdateRequest,
)
from app.shared.service import BaseService

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("uploads/destinations")


def build_destination_embedding_text(destination: Destination) -> str:
    """
    Combine destination name, city, country, description, and tags into a single
    searchable text string for vector embedding generation.
    """
    parts = []
    if destination.name:
        parts.append(f"Name: {destination.name}")
    if destination.city:
        parts.append(f"City: {destination.city}")
    if destination.country:
        parts.append(f"Country: {destination.country}")
    if destination.description:
        parts.append(f"Description: {destination.description}")
    if destination.tags:
        parts.append(f"Tags: {', '.join(destination.tags)}")
    return "\n".join(parts)


class DestinationService(BaseService[DestinationRepository]):
    """Service layer for destination operations including semantic vector search."""

    def __init__(
        self,
        repository: DestinationRepository,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        super().__init__(repository=repository)
        self.embedding_service = embedding_service or EmbeddingService()
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # ── Read Operations ───────────────────────────────────────────────────────

    async def search_destinations(
        self,
        skip: int = 0,
        limit: int = 20,
        query: str | None = None,
        country: str | None = None,
        tag: str | None = None,
        sort_by: str = "name",
        sort_desc: bool = False,
        is_admin: bool = False,
    ) -> DestinationPaginatedResponse:
        """
        Search destinations using a hybrid approach:
        Step 1: Perform exact SQL ILIKE search.
        Step 2: If SQL search returns 0 results and a query string exists,
                fall back to pgvector semantic cosine similarity search.
        """
        # Guard against arbitrary column injection via sort_by.
        valid_sort_fields = {"name", "country", "avg_budget", "created_at", "duration_days"}
        if sort_by not in valid_sort_fields:
            sort_by = "name"

        # Step 1: Perform exact SQL search
        items, total = await self.repository.search(
            skip=skip,
            limit=limit,
            query=query,
            country=country,
            tag=tag,
            sort_by=sort_by,
            sort_desc=sort_desc,
            include_inactive=is_admin,
        )

        # Step 2: Fallback to vector search if query provided and SQL returns no results
        if total == 0 and query and query.strip():
            try:
                query_embedding = await self.embedding_service.generate_embedding(query)
                if query_embedding:
                    vec_items, vec_total = await self.repository.vector_search(
                        query_embedding=query_embedding,
                        skip=skip,
                        limit=limit,
                        country=country,
                        tag=tag,
                    )
                    if vec_items:
                        response_items = []
                        for dest, score in vec_items:
                            resp = DestinationResponse.model_validate(dest)
                            resp.similarity_score = round(score, 4)
                            response_items.append(resp)

                        return DestinationPaginatedResponse(
                            items=response_items,
                            total=vec_total,
                            skip=skip,
                            limit=limit,
                        )
            except Exception as e:
                logger.warning("Vector search fallback skipped/failed: %s", str(e))

        return DestinationPaginatedResponse(
            items=[DestinationResponse.model_validate(item) for item in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_destination(
        self, destination_id: UUID, is_admin: bool = False
    ) -> DestinationResponse:
        """Fetch a single destination by ID."""
        destination = await self.repository.get_by_id(destination_id)
        if not destination or destination.is_deleted:
            raise ResourceNotFoundException("Destination not found.")
        return DestinationResponse.model_validate(destination)

    async def get_count(self) -> DestinationCountResponse:
        """Return the total count of active destinations (for dashboard)."""
        total = await self.repository.get_count()
        return DestinationCountResponse(total=total)

    # ── Write Operations ──────────────────────────────────────────────────────

    async def create_destination(
        self, payload: DestinationCreateRequest
    ) -> DestinationResponse:
        """Create a new destination catalog entry and generate its embedding (Admin only)."""
        logger.info("DestinationService.create_destination: name=%s", payload.name)

        if await self.repository.name_exists(payload.name):
            raise ResourceAlreadyExistsException(
                "A destination with this name already exists."
            )

        destination = Destination(
            id=uuid.uuid4(),
            name=payload.name.strip(),
            country=payload.country.strip(),
            city=payload.city.strip() if payload.city else None,
            description=payload.description.strip(),
            image_url=payload.image_url,
            best_time_to_visit=payload.best_time_to_visit,
            avg_budget=payload.avg_budget,
            duration_days=payload.duration_days,
            tags=payload.tags or [],
        )

        # Generate embedding for the new destination
        try:
            embed_text = build_destination_embedding_text(destination)
            destination.embedding = await self.embedding_service.generate_embedding(embed_text)
        except Exception as e:
            logger.warning("Failed to generate embedding during create: %s", str(e))

        created = await self.repository.create(destination)
        return DestinationResponse.model_validate(created)

    async def update_destination(
        self, destination_id: UUID, payload: DestinationUpdateRequest
    ) -> DestinationResponse:
        """Partially update a destination and refresh its embedding (Admin only)."""
        logger.info("DestinationService.update_destination: id=%s", destination_id)

        destination = await self.repository.get_by_id(destination_id)
        if not destination or destination.is_deleted:
            raise ResourceNotFoundException("Destination not found.")

        # Name uniqueness check — skip if name unchanged.
        if payload.name and payload.name.strip() != destination.name:
            if await self.repository.name_exists(
                payload.name, exclude_id=destination_id
            ):
                raise ResourceAlreadyExistsException(
                    "A destination with this name already exists."
                )
            destination.name = payload.name.strip()

        if payload.country is not None:
            destination.country = payload.country.strip()
        if payload.city is not None:
            destination.city = payload.city.strip()
        if payload.description is not None:
            destination.description = payload.description.strip()
        if payload.image_url is not None:
            destination.image_url = payload.image_url
        if payload.best_time_to_visit is not None:
            destination.best_time_to_visit = payload.best_time_to_visit
        if payload.avg_budget is not None:
            destination.avg_budget = payload.avg_budget
        if payload.duration_days is not None:
            destination.duration_days = payload.duration_days
        if payload.tags is not None:
            destination.tags = payload.tags

        # Regenerate embedding with updated details
        try:
            embed_text = build_destination_embedding_text(destination)
            destination.embedding = await self.embedding_service.generate_embedding(embed_text)
        except Exception as e:
            logger.warning("Failed to generate embedding during update: %s", str(e))

        updated = await self.repository.update(destination)
        return DestinationResponse.model_validate(updated)

    async def bulk_generate_embeddings(self) -> dict[str, Any]:
        """
        Generate and store embeddings for all existing active destinations.
        Admin batch endpoint.
        """
        destinations = await self.repository.get_all_active_destinations()
        if not destinations:
            return {"processed": 0, "message": "No active destinations found."}

        texts = [build_destination_embedding_text(d) for d in destinations]
        embeddings = await self.embedding_service.generate_embeddings(texts)

        for dest, embedding in zip(destinations, embeddings):
            dest.embedding = embedding
            await self.repository.update(dest)

        return {
            "processed": len(destinations),
            "message": f"Successfully generated embeddings for {len(destinations)} destinations.",
        }

    async def delete_destination(self, destination_id: UUID) -> None:
        """Soft-delete a destination (Admin only)."""
        logger.info("DestinationService.delete_destination: id=%s", destination_id)
        destination = await self.repository.get_by_id(destination_id)
        if not destination or destination.is_deleted:
            raise ResourceNotFoundException("Destination not found.")

        destination.soft_delete()
        await self.repository.update(destination)

    async def upload_image(
        self, destination_id: UUID, file: UploadFile
    ) -> DestinationResponse:
        """Upload and attach a cover image to a destination (Admin only)."""
        logger.info("DestinationService.upload_image: id=%s", destination_id)
        destination = await self.repository.get_by_id(destination_id)
        if not destination or destination.is_deleted:
            raise ResourceNotFoundException("Destination not found.")

        allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        file_ext = Path(file.filename).suffix.lower() if file.filename else ""
        if file_ext not in allowed_extensions:
            raise ValidationException(
                message="Invalid file type.",
                detail=f"Allowed extensions: {', '.join(allowed_extensions)}",
            )

        filename = f"{destination_id}{file_ext}"
        file_path = UPLOAD_DIR / filename

        try:
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as exc:
            logger.error("Failed to save image: %s", exc)
            raise BusinessRuleViolationException("Could not process the uploaded file.")
        finally:
            file.file.close()

        # We serve the uploads/ directory at /uploads in main.py.
        destination.image_url = f"/uploads/destinations/{filename}"
        updated = await self.repository.update(destination)
        return DestinationResponse.model_validate(updated)
