"""
app/worker.py

Celery application initialization for background tasks.
"""

import os
from celery import Celery

# Use Redis running locally on default port 6379
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "tripmate_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Auto-discover tasks from the PDF module
    imports=["app.modules.pdf.tasks"],
)
