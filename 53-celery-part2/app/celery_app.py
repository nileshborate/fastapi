# The Celery app - now with a SCHEDULE for celery beat
from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery("course_hub", broker=settings.broker_url, backend=settings.result_backend,
                    include=["app.tasks"])
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=3600,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    timezone="Asia/Kolkata",                       # crontab times are Indian time
    beat_schedule={
        "heartbeat-every-5-seconds": {             # a name for the log
            "task": "app.tasks.heartbeat",
            "schedule": 5.0,                       # every 5 seconds
        },
        "daily-digest-7-30": {
            "task": "app.tasks.daily_digest",
            "schedule": crontab(hour=7, minute=30),          # every day at 07:30
        },
        "cleanup-2-am": {                          # homework 53
            "task": "app.tasks.cleanup",
            "schedule": crontab(hour=2, minute=0),
        },
        "weekly-report-monday": {
            "task": "app.tasks.daily_digest",
            "schedule": crontab(hour=9, minute=0, day_of_week="mon"),
            "kwargs": {"weekly": True},
        },
    },
)
