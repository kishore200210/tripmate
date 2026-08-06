"""
app/modules/pdf/tasks.py

Celery tasks for PDF Generation using WeasyPrint.
"""

import asyncio
import logging
import os
import uuid
from itertools import groupby

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.db.session import AsyncSessionLocal
from app.modules.itineraries.repository import ItineraryRepository
from app.modules.trips.repository import TripRepository
from app.celery_app import celery_app

logger = logging.getLogger(__name__)

# Setup Jinja2 environment pointing to the templates directory
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

# Ensure pdf output directory exists
PDF_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "uploads", "pdfs")
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)


async def _generate_itinerary_pdf_async(trip_id: str) -> str:
    """Async business logic for fetching data and generating PDF."""
    async with AsyncSessionLocal() as session:
        trip_repo = TripRepository(db=session)
        itinerary_repo = ItineraryRepository(db=session)

        # 1. Fetch Trip
        trip = await trip_repo.get_by_id(uuid.UUID(trip_id))
        if not trip or trip.is_deleted:
            raise ValueError(f"Trip with id {trip_id} not found or deleted.")

        # 2. Fetch Itinerary Items
        items = await itinerary_repo.get_trip_itinerary(uuid.UUID(trip_id))

        # 3. Group items by day_no
        grouped_items = {}
        for day, group in groupby(items, key=lambda x: x.day_no):
            grouped_items[day] = list(group)

        # 4. Render HTML template
        template = jinja_env.get_template("itinerary.html")
        html_out = template.render(
            trip=trip,
            grouped_items=grouped_items
        )

        # 5. Generate PDF
        file_name = f"itinerary_{trip_id}.pdf"
        file_path = os.path.join(PDF_OUTPUT_DIR, file_name)
        
        # WeasyPrint can be slow, but it runs synchronously.
        # This is fine because we are running inside a Celery worker thread.
        HTML(string=html_out).write_pdf(file_path)

        return file_path


@celery_app.task(name="generate_itinerary_pdf", bind=True)
def generate_itinerary_pdf(self, trip_id: str) -> dict:
    """
    Celery task to generate an itinerary PDF.
    Wraps async repository logic into the synchronous Celery worker loop.
    """
    logger.info(f"Task {self.request.id}: Generating PDF for Trip {trip_id}")
    try:
        # Run async function in sync wrapper
        file_path = asyncio.run(_generate_itinerary_pdf_async(trip_id))
        return {"status": "SUCCESS", "file_path": file_path}
    except Exception as e:
        logger.error(f"Task {self.request.id}: PDF generation failed: {str(e)}")
        # Re-raise to let Celery handle the FAILURE state properly
        raise
