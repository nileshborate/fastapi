# The Celery app: FastAPI (who SENDS tasks) and the worker (who RUNS them) both import it
from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "course_hub",
    broker=settings.broker_url,                    # Redis list "celery" = the queue
    backend=settings.result_backend,               # celery-task-meta-<id> = the result
    include=["app.tasks"],                         # the worker imports our tasks from here
)
celery_app.conf.update(
    task_serializer="json",                        # arguments travel as JSON - keep them simple
    result_serializer="json",
    accept_content=["json"],
    result_expires=3600,                           # results are deleted after 1 hour
    task_track_started=True,                       # PENDING -> STARTED -> SUCCESS
    broker_connection_retry_on_startup=True,
)
