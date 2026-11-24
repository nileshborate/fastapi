# Video 59 - Course Hub on PostgreSQL: the database is its own service in Compose
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from pydantic import BaseModel, Field

from app.config import get_settings
from app.db import Database

settings = get_settings()
db = Database(settings.database_url)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    db.open(wait_s=settings.db_wait_s)        # no database -> the app does not start
    yield
    db.close()


app = FastAPI(title="Course Hub", lifespan=lifespan)


class CourseIn(BaseModel):
    title: str = Field(min_length=3, max_length=80)


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/health/ready")
def ready(response: Response) -> dict[str, str]:
    if not db.ping():
        response.status_code = 503
        return {"status": "not_ready", "database": "unreachable"}
    return {"status": "ready", "version": settings.version}


@app.get("/courses")
def courses() -> list[dict]:
    return db.list_courses()


@app.post("/courses", status_code=201)
def create_course(data: CourseIn) -> dict:
    return db.add_course(data.title)
