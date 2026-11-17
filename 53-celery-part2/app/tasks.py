# Retries, a canvas (chain · group · chord) and scheduled tasks
import time

from celery.utils.log import get_task_logger

from app import email_server, store
from app.celery_app import celery_app
from app.config import get_settings

log = get_task_logger(__name__)
COURSES = {1: ("Python Basics", 1200), 2: ("SQL Joins", 800), 3: ("FastAPI Mastery", 2500)}


# ----------------------------------------------------------------------------- 1. retries
@celery_app.task(
    bind=True,
    autoretry_for=(email_server.EmailServerDown,),   # retry ONLY temporary errors
    retry_backoff=1,                                 # wait 1 s, 2 s, 4 s, 8 s ...
    retry_backoff_max=30,                            # ... but never more than 30 s
    retry_jitter=False,                              # (True in production: random waits)
    max_retries=3,                                   # 1 try + 3 retries, then FAILURE
)
def send_email(self, to: str) -> dict[str, int | str | bool]:
    log.info("sending to %s (retry %s)", to, self.request.retries)
    notes = store.get_store()
    key = f"sent:{to}"
    if not notes.set(key, "sending", nx=True, ex=3600):   # homework 53: only ONCE per hour
        return {"to": to, "skipped": True}
    try:
        attempt = email_server.send(to, "Your report is ready")
    except Exception:
        notes.delete(key)              # it was NOT sent: free the key, so a retry can try again
        raise
    return {"to": to, "attempts": attempt}


# ----------------------------------------------------------------------------- 2. a canvas
@celery_app.task
def load_course(course_id: int) -> dict[str, int | str]:
    time.sleep(get_settings().step_seconds)           # a slow query
    title, students = COURSES[course_id]
    return {"course_id": course_id, "title": title, "students": students}


@celery_app.task
def make_report(course: dict[str, int | str]) -> dict[str, int | str]:
    time.sleep(get_settings().step_seconds)           # build a file
    return {**course, "file": f"report-{course['course_id']}.csv"}


@celery_app.task
def notify(report: dict[str, int | str], email: str) -> str:
    time.sleep(get_settings().step_seconds)
    return f"{report['file']} sent to {email}"


@celery_app.task
def summarize(courses: list[dict[str, int | str]]) -> dict[str, int]:
    return {"courses": len(courses), "students": sum(int(c["students"]) for c in courses)}


# ----------------------------------------------------------------------------- 3. scheduled
@celery_app.task
def heartbeat() -> str:
    now = celery_app.now().strftime("%H:%M:%S")       # in the app's timezone (Asia/Kolkata)
    store.get_store().rpush("heartbeats", now)        # for the demo
    return now


@celery_app.task
def daily_digest(weekly: bool = False) -> str:
    return "weekly report sent" if weekly else "daily digest sent"


@celery_app.task                                       # homework 53: beat runs it at 02:00
def cleanup() -> int:
    notes = store.get_store()
    removed = notes.llen("heartbeats")
    notes.delete("heartbeats")
    return removed
