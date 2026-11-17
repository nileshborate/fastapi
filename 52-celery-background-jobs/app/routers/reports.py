# A long job: 202 Accepted + where to ask for the status
from typing import Annotated

from fastapi import APIRouter, Path, Query, Response, status

from app.schemas import TaskStatus
from app.tasks import build_multi_report, build_report

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/{course_id}", status_code=status.HTTP_202_ACCEPTED)
def start_report(course_id: Annotated[int, Path(ge=1, le=1_000_000)],
                 response: Response) -> TaskStatus:
    task = build_report.delay(course_id)
    response.headers["Location"] = f"/tasks/{task.id}"      # "ask here"
    return TaskStatus(task_id=task.id, state="PENDING")


@router.post("", status_code=status.HTTP_202_ACCEPTED)                  # homework 52
def start_multi_report(course_ids: Annotated[list[int], Query(min_length=1, max_length=10)],
                       response: Response) -> TaskStatus:
    task = build_multi_report.delay(course_ids)             # a list of ints is JSON too
    response.headers["Location"] = f"/tasks/{task.id}"
    return TaskStatus(task_id=task.id, state="PENDING")
