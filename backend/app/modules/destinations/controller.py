"""
app/modules/destinations/controller.py

Destination Controller — thin HTTP translation layer.

Responsibilities:
    - Translates HTTP request parameters into service calls.
    - Does NOT contain business logic — delegates entirely to DestinationService.
    - Returns typed response schemas — never raw model instances.
"""

from uuid import UUID

from fastapi import UploadFile

from app.modules.auth.schemas import MessageResponse
from app.modules.destinations.schemas import (
    DestinationCountResponse,
    DestinationCreateRequest,
    DestinationPaginatedResponse,
    DestinationResponse,
    DestinationUpdateRequest,
)
from app.modules.destinations.service import DestinationService


class DestinationController:
    """Thin HTTP controller — no business logic, only delegation to the service layer."""

    @staticmethod
    async def count_destinations(
        service: DestinationService,
    ) -> DestinationCountResponse:
        return await service.get_count()

    @staticmethod
    async def search_destinations(
        skip: int,
        limit: int,
        query: str | None,
        country: str | None,
        tag: str | None,
        sort_by: str,
        sort_desc: bool,
        service: DestinationService,
        is_admin: bool = False,
    ) -> DestinationPaginatedResponse:
        return await service.search_destinations(
            skip=skip,
            limit=limit,
            query=query,
            country=country,
            tag=tag,
            sort_by=sort_by,
            sort_desc=sort_desc,
            is_admin=is_admin,
        )

    @staticmethod
    async def get_destination(
        destination_id: UUID, service: DestinationService, is_admin: bool = False
    ) -> DestinationResponse:
        return await service.get_destination(destination_id, is_admin=is_admin)

    @staticmethod
    async def create_destination(
        payload: DestinationCreateRequest, service: DestinationService
    ) -> DestinationResponse:
        return await service.create_destination(payload)

    @staticmethod
    async def update_destination(
        destination_id: UUID,
        payload: DestinationUpdateRequest,
        service: DestinationService,
    ) -> DestinationResponse:
        return await service.update_destination(destination_id, payload)

    @staticmethod
    async def delete_destination(
        destination_id: UUID, service: DestinationService
    ) -> MessageResponse:
        await service.delete_destination(destination_id)
        return MessageResponse(message="Destination deleted successfully.")

    @staticmethod
    async def upload_image(
        destination_id: UUID, file: UploadFile, service: DestinationService
    ) -> DestinationResponse:
        return await service.upload_image(destination_id, file)

    @staticmethod
    async def generate_all_embeddings(
        service: DestinationService,
    ) -> dict:
        return await service.bulk_generate_embeddings()
