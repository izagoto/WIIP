import os
import sys
from celery import Celery

# Ensure backend folder is in PYTHONPATH so Celery can discover 'app' modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.core.config import settings

celery_app = Celery(
    "wiip_worker",
    broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # Make sure we import tasks
    imports=[
        "worker.tasks.evidence_parser"
    ]
)
