from typing import Any

from pydantic import BaseModel, EmailStr


class EmailIn(BaseModel):
    to: EmailStr


class TaskStatus(BaseModel):
    task_id: str
    state: str                     # PENDING · STARTED · RETRY · SUCCESS · FAILURE
    result: Any = None
    error: str | None = None
