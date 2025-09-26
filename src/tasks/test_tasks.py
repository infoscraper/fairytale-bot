"""Test tasks for Celery"""
import time
from ..core.celery_app import celery_app


@celery_app.task
def test_task(duration: int = 5):
    """Тестовая задача для проверки Celery"""
    time.sleep(duration)
    return f"✅ Task completed after {duration} seconds"


@celery_app.task
def add_numbers(x: int, y: int):
    """Простая задача сложения"""
    return x + y
