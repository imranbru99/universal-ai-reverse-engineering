from celery import Celery

from app.config import get_settings

settings = get_settings()

app = Celery(
    "reverseforge",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["workers.tasks.pipeline"],
)

app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)
