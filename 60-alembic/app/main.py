# Video 60 - Course Hub 1.8.0: the schema comes from Alembic migrations, never from the app
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, Response
from pydantic import BaseModel, Field

from app.config import get_settings
from app.db import Database, head_revision

settings = get_settings()
db = Database(settings.database_url)
HEAD = head_revision()          # e.g. "0003" - read once, from the migrations folder


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    db.open(wait_s=settings.db_wait_s)        # no CREATE TABLE here any more
    yield
    db.close()


app = FastAPI(title="Course Hub", lifespan=lifespan)


class CourseIn(BaseModel):
    title: str = Field(min_length=3, max_length=80)
    description: str | None = Field(default=None, max_length=500)
    level: Literal["beginner", "intermediate", "advanced"] = "beginner"     # 0002


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/health/ready")
def ready(response: Response) -> dict[str, str]:
    current = db.revision()
    if current is None:
        response.status_code = 503
        return {"status": "not_ready", "database": "unreachable"}
    if current != HEAD:                                   # old schema: don't send traffic here
        response.status_code = 503
        return {"status": "not_ready", "database": "migrations pending",
                "revision": current or "none", "expected": HEAD}
    return {"status": "ready", "version": settings.version, "revision": current}


@app.get("/courses")
def courses() -> list[dict]:
    return db.list_courses()


@app.post("/courses", status_code=201)
def create_course(data: CourseIn) -> dict:
    return db.add_course(data.title, data.description, data.level)
