# Tasks: normal (sync) Python functions - Celery runs them in the WORKER, not in FastAPI
import time
from datetime import UTC, datetime

from celery.utils.log import get_task_logger

from app.celery_app import celery_app
from app.config import get_settings

log = get_task_logger(__name__)
COURSES = {1: ("Python Basics", 1200), 2: ("SQL Joins", 800), 3: ("FastAPI Mastery", 2500)}


def send_email(to: str, subject: str) -> None:
    """a slow email server: the network + the SMTP conversation"""
    time.sleep(get_settings().email_seconds)
    log.info("email sent to %s: %s", to, subject)


@celery_app.task
def send_welcome_email(email: str, name: str) -> dict[str, str]:
    send_email(email, f"Welcome to Course Hub, {name}!")
    return {"to": email, "sent_at": datetime.now(UTC).isoformat(timespec="seconds")}


@celery_app.task(bind=True)                        # bind=True: self = the running task
def build_report(self, course_id: int) -> dict[str, int | str]:
    if course_id not in COURSES:
        raise ValueError(f"course {course_id} not found")     # -> state FAILURE
    title, students = COURSES[course_id]
    for step in range(1, 6):
        time.sleep(get_settings().report_step_seconds)        # one slow part of the report
        self.update_state(state="PROGRESS", meta={"step": step, "of": 5})
    return {"course_id": course_id, "title": title, "students": students, "rows": students * 4}


@celery_app.task                                   # homework 52
def send_reminder(email: str) -> dict[str, str]:
    send_email(email, "We miss you at Course Hub!")
    return {"to": email, "sent_at": datetime.now(UTC).isoformat(timespec="seconds")}


@celery_app.task(bind=True)                        # homework 52: several courses, one task
def build_multi_report(self, course_ids: list[int]) -> list[dict[str, int | str]]:
    reports = []
    for done, course_id in enumerate(course_ids, start=1):
        if course_id not in COURSES:
            raise ValueError(f"course {course_id} not found")
        title, students = COURSES[course_id]
        time.sleep(get_settings().report_step_seconds)
        reports.append({"course_id": course_id, "title": title, "students": students})
        self.update_state(state="PROGRESS",
                          meta={"course": course_id, "done": done, "of": len(course_ids)})
    return reports
