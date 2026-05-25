"""Celery entrypoint. Run via:
    celery -A celery_worker.celery worker
    celery -A celery_worker.celery beat
"""
from app import create_app
from app.extensions import celery as _celery

flask_app = create_app()
flask_app.app_context().push()
celery = _celery
