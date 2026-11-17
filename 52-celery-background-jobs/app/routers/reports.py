# A long job: 202 Accepted + where to ask for the status
from typing import Annotated

from fastapi import APIRouter, Path, Response, status

from app.schemas import TaskStatus
from app.tasks import build_report

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/{course_id}", status_code=status.HTTP_202_ACCEPTED)
def start_report(course_id: Annotated[int, Path(ge=1, le=1_000_000)],
                 response: Response) -> TaskStatus:
    task = build_report.delay(course_id)
    response.headers["Location"] = f"/tasks/{task.id}"      # "ask here"
    return TaskStatus(task_id=task.id, state="PENDING")
