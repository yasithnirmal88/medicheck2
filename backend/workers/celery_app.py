from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "medicheck",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

celery_app.conf.task_routes = {
    "workers.tasks.assessment_tasks.*": {"queue": "assessments"},
    "workers.tasks.notification_tasks.*": {"queue": "notifications"},
}

celery_app.conf.beat_schedule = {
    "cleanup-expired-sessions": {
        "task": "workers.tasks.assessment_tasks.cleanup_expired_data",
        "schedule": 3600.0,
    },
}

celery_app.autodiscover_tasks(["workers.tasks"])


@celery_app.task(name="workers.celery_app.health_check")
def health_check() -> str:
    return "celery-healthy"
