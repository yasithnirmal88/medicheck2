from __future__ import annotations

from app.core.logging import get_logger
from workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(name="workers.tasks.assessment_tasks.cleanup_expired_data")
def cleanup_expired_data() -> dict:
    logger.info("Starting cleanup of expired data")
    results = {
        "deleted_sessions": 0,
        "deleted_tokens": 0,
        "status": "completed",
    }
    logger.info("Cleanup completed: %s", results)
    return results


@celery_app.task(
    name="workers.tasks.assessment_tasks.process_assessment",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_assessment(self, assessment_id: str) -> dict:
    logger.info("Processing assessment: %s", assessment_id)
    try:
        result = {
            "assessment_id": assessment_id,
            "status": "completed",
            "score": 0.0,
        }
        logger.info("Assessment processed: %s", result)
        return result
    except Exception as exc:
        logger.error("Failed to process assessment %s: %s", assessment_id, exc)
        raise self.retry(exc=exc) from exc


@celery_app.task(name="workers.tasks.assessment_tasks.send_notification")
def send_notification(user_id: str, notification_type: str, payload: dict) -> dict:
    logger.info(
        "Sending %s notification to user %s",
        notification_type,
        user_id,
    )
    return {
        "user_id": user_id,
        "notification_type": notification_type,
        "status": "sent",
    }
