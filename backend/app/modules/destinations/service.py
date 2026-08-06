"""
app/modules/destinations/service.py

Destination Service — business logic for destination management.
"""

import logging
import os
import shutil
import uuid
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import (
    BusinessRuleViolationException,
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
    ValidationException,
)
from app.modules.destinations.models import Destination
from app.modules.destinations.repository import DestinationRepository
from app.modules.destinations.schemas import (
    DestinationCreateRequest,
    DestinationPaginatedResponse,
    DestinationResponse,
    DestinationUpdateRequest,
)
from app.shared.service import BaseService

logger = logging.getLogger(__name__)
settings = get_settings()

UPLOAD_DIR = Path("uploads/destinations")


class DestinationService(BaseService[DestinationRepository]):
    """Service layer for destination operations."""

    def __init__(self, repository: DestinationRepository) -> None:
        super().__init__(repository=repository)
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

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
        """Search destinations with filtering and pagination."""
        valid_sort_fields = {"name", "country", "avg_budget", "created_at"}
        if sort_by not in valid_sort_fields:
            sort_by = "name"

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

        return DestinationPaginatedResponse(
            items=[DestinationResponse.model_validate(item) for item in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_destination(self, destination_id: UUID, is_admin: bool = False) -> DestinationResponse:
        """Get a single destination by ID."""
        destination = await self.repository.get_by_id(destination_id)
        if not destination or destination.is_deleted:
            raise ResourceNotFoundException("Destination not found.")
            
        return DestinationResponse.model_validate(destination)

    async def create_destination(self, payload: DestinationCreateRequest) -> DestinationResponse:
        """Create a new destination (Admin only)."""
        logger.info("DestinationService.create_destination: %s", payload.name)
        
        if await self.repository.name_exists(payload.name):
            raise ResourceAlreadyExistsException("A destination with this name already exists.")

        destination = Destination(
            id=uuid.uuid4(),
            name=payload.name.strip(),
            country=payload.country.strip(),
            description=payload.description.strip(),
            avg_budget=payload.avg_budget,
            tags=payload.tags,
        )
        created = await self.repository.create(destination)
        return DestinationResponse.model_validate(created)

    async def update_destination(
        self, destination_id: UUID, payload: DestinationUpdateRequest
    ) -> DestinationResponse:
        """Update an existing destination (Admin only)."""
        logger.info("DestinationService.update_destination: id=%s", destination_id)
        
        destination = await self.repository.get_by_id(destination_id)
        if not destination or destination.is_deleted:
            raise ResourceNotFoundException("Destination not found.")

        if payload.name and payload.name.strip() != destination.name:
            if await self.repository.name_exists(payload.name, exclude_id=destination_id):
                raise ResourceAlreadyExistsException("A destination with this name already exists.")
            destination.name = payload.name.strip()

        if payload.country is not None:
            destination.country = payload.country.strip()
        if payload.description is not None:
            destination.description = payload.description.strip()
        if payload.avg_budget is not None:
            destination.avg_budget = payload.avg_budget
        if payload.tags is not None:
            destination.tags = payload.tags

        updated = await self.repository.update(destination)
        return DestinationResponse.model_validate(updated)

    async def delete_destination(self, destination_id: UUID) -> None:
        """Soft-delete a destination (Admin only)."""
        logger.info("DestinationService.delete_destination: id=%s", destination_id)
        destination = await self.repository.get_by_id(destination_id)
        if not destination or destination.is_deleted:
            raise ResourceNotFoundException("Destination not found.")

        destination.soft_delete()
        await self.repository.update(destination)

    async def upload_image(self, destination_id: UUID, file: UploadFile) -> DestinationResponse:
        """Upload and attach an image to a destination (Admin only)."""
        logger.info("DestinationService.upload_image: id=%s", destination_id)
        destination = await self.repository.get_by_id(destination_id)
        if not destination or destination.is_deleted:
            raise ResourceNotFoundException("Destination not found.")

        # Validate file extension
        allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        file_ext = Path(file.filename).suffix.lower() if file.filename else ""
        if file_ext not in allowed_extensions:
            raise ValidationException(
                message="Invalid file type.",
                detail=f"Allowed extensions are: {', '.join(allowed_extensions)}"
            )

        # Generate safe filename and save to local disk
        filename = f"{destination_id}{file_ext}"
        file_path = UPLOAD_DIR / filename
        
        try:
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            logger.error("Failed to save image file: %s", e)
            raise BusinessRuleViolationException("Could not process the uploaded file.")
        finally:
            file.file.close()

        # Update destination with the new relative URL
        # We serve the `uploads` directory at the `/uploads` URL prefix in main.py
        destination.image_url = f"/uploads/destinations/{filename}"
        updated = await self.repository.update(destination)
        
        return DestinationResponse.model_validate(updated)
