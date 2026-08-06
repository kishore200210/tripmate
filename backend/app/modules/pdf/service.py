"""
app/modules/pdf/service.py

PDF Service — handles task dispatching and status tracking.
"""

import logging
from uuid import UUID

from celery.result import AsyncResult

from app.core.exceptions import ResourceNotFoundException
from app.modules.pdf.schemas import TaskResponse, TaskStatusResponse
from app.modules.pdf.tasks import generate_itinerary_pdf
from app.modules.trips.repository import TripRepository
from app.modules.users.models import User
from app.celery_app import celery_app

logger = logging.getLogger(__name__)


class PDFService:
    """Service layer for offloading PDF generation to Celery."""

    def __init__(self, trip_repository: TripRepository) -> None:
        self.trip_repository = trip_repository

    async def trigger_itinerary_pdf(self, trip_id: UUID, current_user: User) -> TaskResponse:
        """Triggers the Celery task after validating trip ownership."""
        trip = await self.trip_repository.get_by_id(trip_id)
        if not trip or trip.is_deleted:
            raise ResourceNotFoundException("Trip not found.")
            
        # Ownership check
        if trip.user_id != current_user.id:
            raise ResourceNotFoundException("Trip not found.")

        # Dispatch task to background worker
        task = generate_itinerary_pdf.delay(str(trip_id))
        
        return TaskResponse(
            task_id=task.id,
            message="PDF generation task queued successfully."
        )

    async def get_task_status(self, task_id: str) -> TaskStatusResponse:
        """Checks the status of a Celery task."""
        # Use Celery's AsyncResult to query the backend (Redis)
        task_result = AsyncResult(task_id, app=celery_app)
        
        # If task failed, task_result.result contains the Exception
        result_data = None
        if task_result.state == 'SUCCESS':
            result_data = task_result.result
        elif task_result.state == 'FAILURE':
            result_data = str(task_result.result)

        return TaskStatusResponse(
            task_id=task_id,
            status=task_result.state,
            result=result_data
        )
