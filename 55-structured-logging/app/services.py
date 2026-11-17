# The business code just logs EVENTS with fields - it knows nothing about request ids
import asyncio
import logging

from fastapi import HTTPException

log = logging.getLogger("app.services")

COURSES = {1: "Python Basics", 2: "SQL Joins", 3: "FastAPI Mastery"}
ENROLLED: set[tuple[str, int]] = set()


def enroll(email: str, course_id: int, card_number: str) -> dict[str, object]:
    if course_id not in COURSES:
        log.warning("enrollment.unknown_course", extra={"course_id": course_id})
        raise HTTPException(status_code=404, detail="Course not found")
    if (email, course_id) in ENROLLED:
        log.info("enrollment.duplicate", extra={"email": email, "course_id": course_id})
        return {"email": email, "course_id": course_id, "new": False}
    log.debug("payment.charging", extra={"card_number": card_number})    # -> "***"
    ENROLLED.add((email, course_id))
    log.info("enrollment.created", extra={"email": email, "course_id": course_id,
                                          "course": COURSES[course_id]})
    return {"email": email, "course_id": course_id, "new": True}


async def build_report(course_id: int) -> dict[str, object]:
    log.info("report.started", extra={"course_id": course_id})
    for step in ("load", "count", "render"):
        await asyncio.sleep(0.1)                         # other requests run meanwhile
        log.info("report.step", extra={"course_id": course_id, "step": step})
    log.info("report.finished", extra={"course_id": course_id})
    return {"course_id": course_id, "students": 3 * course_id}
