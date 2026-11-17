# Ask Celery's result backend how a task is doing
from uuid import UUID

from celery.result import AsyncResult
from fastapi import APIRouter

from app.celery_app import celery_app
from app.schemas import TaskStatus

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/{task_id}")
def task_status(task_id: UUID) -> TaskStatus:        # def: AsyncResult does blocking Redis I/O
    result = AsyncResult(str(task_id), app=celery_app)
    status = TaskStatus(task_id=str(task_id), state=result.state)
    if result.state == "PROGRESS":
        status.progress = result.info                 # the meta from update_state
    elif result.successful():
        status.result = result.result                 # the return value
    elif result.failed():
        status.error = repr(result.result)            # the exception
    return status
