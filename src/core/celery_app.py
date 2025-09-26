"""Celery app configuration"""
from celery import Celery
from .config import settings

# Create Celery instance
celery_app = Celery(
    "fairytale_bot",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
    task_routes={
        "src.tasks.test_tasks.*": {"queue": "test"},
    }
)

# Auto-discover tasks
celery_app.autodiscover_tasks(['src.tasks'])
