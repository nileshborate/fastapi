# Endpoints that start a retrying task, a chain and a chord - and read any task's status
from typing import Annotated
from uuid import UUID

from celery import chain, chord, group
from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, Path, Query, Response, status
from pydantic import EmailStr

from app.celery_app import celery_app
from app.schemas import EmailIn, TaskStatus
from app.tasks import COURSES, load_course, make_report, notify, send_email, summarize

router = APIRouter(tags=["Jobs"])
CourseId = Annotated[int, Path(ge=1, le=3)]


def accepted(task_id: str, response: Response) -> TaskStatus:
    response.headers["Location"] = f"/tasks/{task_id}"
    return TaskStatus(task_id=task_id, state="PENDING")


@router.post("/emails", status_code=status.HTTP_202_ACCEPTED)
def queue_email(data: EmailIn, response: Response) -> TaskStatus:
    return accepted(send_email.delay(data.to).id, response)


@router.post("/reports/{course_id}/pipeline", status_code=status.HTTP_202_ACCEPTED)
def report_pipeline(course_id: CourseId, email: EmailStr, response: Response) -> TaskStatus:
    # chain: each result goes INTO the next task -> load -> make_report -> notify
    workflow = chain(load_course.s(course_id), make_report.s(), notify.s(email))
    return accepted(workflow.apply_async().id, response)        # the id of the LAST task


@router.post("/reports/summary", status_code=status.HTTP_202_ACCEPTED)
def report_summary(response: Response,
                   course_ids: Annotated[list[int], Query(min_length=1, max_length=3)]
                   ) -> TaskStatus:
    unknown = [c for c in course_ids if c not in COURSES]
    if unknown:                                          # check before queueing (Video 52)
        raise HTTPException(status_code=404, detail=f"Unknown courses: {unknown}")
    # chord: a GROUP runs in parallel, then ONE callback gets all the results
    workflow = chord(group(load_course.s(c) for c in course_ids), summarize.s())
    return accepted(workflow.apply_async().id, response)


@router.get("/tasks/{task_id}")
def task_status(task_id: UUID) -> TaskStatus:
    result = AsyncResult(str(task_id), app=celery_app)
    out = TaskStatus(task_id=str(task_id), state=result.state)
    if result.successful():
        out.result = result.result
    elif result.state in ("FAILURE", "RETRY"):
        out.error = repr(result.result)                # the (last) exception
    return out
