web: python init_db.py && python -m src.main
worker: celery -A src.core.celery_app worker --loglevel=info
