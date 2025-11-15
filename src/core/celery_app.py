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
# Celery expects packages that contain a 'tasks' submodule. Our project has
# 'src/tasks', so we should pass the parent package 'src' (not 'src.tasks').
celery_app.autodiscover_tasks(['src'])

# As a safety net in non-standard runtimes, import task modules explicitly.
try:  # pragma: no cover
    import src.tasks.story_tasks  # noqa: F401
    import src.tasks.test_tasks  # noqa: F401
except Exception:  # Import errors should not crash worker startup
    pass
