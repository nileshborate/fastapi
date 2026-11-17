# Watch the workers from your API: who is alive, and what are they doing right now?
from typing import Any

from fastapi import APIRouter, Response, status

from app.celery_app import celery_app

router = APIRouter(prefix="/workers", tags=["Workers"])


@router.get("")
def workers(response: Response) -> dict[str, Any]:
    inspect = celery_app.control.inspect(timeout=1.0)     # asks every worker, waits 1 s
    active = inspect.active() or {}                       # None when no worker answers
    if not active:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "workers": sorted(active),
        "active": {name: [t["name"] for t in tasks] for name, tasks in active.items()},
    }
