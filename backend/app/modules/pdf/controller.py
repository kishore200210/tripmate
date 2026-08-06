"""
app/modules/pdf/controller.py

PDF Controller — HTTP translation layer for the PDF service.
"""

import os
from uuid import UUID

from fastapi import HTTPException
from fastapi.responses import FileResponse

from app.modules.pdf.schemas import TaskResponse, TaskStatusResponse
from app.modules.pdf.service import PDFService
from app.modules.users.models import User


class PDFController:
    """HTTP controller for the PDF module."""

    @staticmethod
    async def trigger_itinerary_pdf(
        trip_id: UUID, service: PDFService, current_user: User
    ) -> TaskResponse:
        return await service.trigger_itinerary_pdf(trip_id, current_user)

    @staticmethod
    async def get_task_status(
        task_id: str, service: PDFService
    ) -> TaskStatusResponse:
        return await service.get_task_status(task_id)

    @staticmethod
    async def download_pdf(
        task_id: str, service: PDFService
    ) -> FileResponse:
        status = await service.get_task_status(task_id)
        
        if status.status != "SUCCESS":
            raise HTTPException(status_code=400, detail="PDF is not ready yet or failed.")
            
        file_path = status.result.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="PDF file not found on disk.")
            
        return FileResponse(
            path=file_path, 
            filename=os.path.basename(file_path),
            media_type="application/pdf"
        )
