from typing import Any

from pydantic import BaseModel, EmailStr, Field


class UserIn(BaseModel):
    email: EmailStr
    name: str = Field(min_length=2, max_length=40)


class Registered(BaseModel):
    email: EmailStr
    task_id: str | None = None                     # the email task - None when sent inline


class TaskStatus(BaseModel):
    task_id: str
    state: str                     # PENDING · STARTED · PROGRESS · SUCCESS · FAILURE
    progress: dict[str, Any] | None = None
    result: Any = None
    error: str | None = None
