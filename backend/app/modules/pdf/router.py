"""
app/modules/pdf/router.py

PDF API Router — URL mapping and Swagger documentation.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.middleware import get_current_user
from app.modules.pdf.controller import PDFController
from app.modules.pdf.schemas import TaskResponse, TaskStatusResponse
from app.modules.pdf.service import PDFService
from app.modules.trips.repository import TripRepository
from app.modules.users.models import User

router = APIRouter(
    prefix="/pdf",
    tags=["PDF Generation"],
)


# ── Dependency Factory ────────────────────────────────────────────────────────

def get_pdf_service(db: AsyncSession = Depends(get_db)) -> PDFService:
    trip_repository = TripRepository(db=db)
    return PDFService(trip_repository=trip_repository)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/itinerary/{trip_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger PDF generation for a trip itinerary",
)
async def generate_itinerary_pdf(
    trip_id: UUID,
    current_user: User = Depends(get_current_user),
    service: PDFService = Depends(get_pdf_service),
) -> TaskResponse:
    """
    Validates trip ownership and dispatches a background Celery task
    to generate a beautiful PDF itinerary. Returns the task ID immediately.
    """
    return await PDFController.trigger_itinerary_pdf(trip_id, service, current_user)


@router.get(
    "/status/{task_id}",
    response_model=TaskStatusResponse,
    summary="Check status of a PDF generation task",
)
async def get_pdf_status(
    task_id: str,
    # Authentication optional for status check if we assume task_ids are unguessable UUIDs.
    service: PDFService = Depends(get_pdf_service),
) -> TaskStatusResponse:
    """Check whether the background task is PENDING, SUCCESS, or FAILURE."""
    return await PDFController.get_task_status(task_id, service)


@router.get(
    "/download/{task_id}",
    response_class=FileResponse,
    summary="Download the generated PDF",
)
async def download_pdf(
    task_id: str,
    service: PDFService = Depends(get_pdf_service),
) -> FileResponse:
    """
    Downloads the actual PDF file once the task is SUCCESS.
    Returns 400 if the task is still processing.
    """
    return await PDFController.download_pdf(task_id, service)
