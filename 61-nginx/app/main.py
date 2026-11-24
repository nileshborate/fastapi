# Video 61 - Course Hub 1.10.1 behind Nginx: links use the scheme + host the CLIENT used
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.config import get_settings
from app.db import Database, head_revision, known_revisions
from app.request_log import RequestLogMiddleware

settings = get_settings()
db = Database(settings.database_url)
HEAD = head_revision()          # e.g. "0005" - read once, from the migrations folder
KNOWN = known_revisions()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    db.open(wait_s=settings.db_wait_s)        # no CREATE TABLE here any more
    yield
    db.close()


app = FastAPI(title="Course Hub", lifespan=lifespan)
app.add_middleware(RequestLogMiddleware)          # homework 61: the request id in our log


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
    # BEHIND = a revision this code knows, but not the head: don't send traffic here.
    # NEWER (unknown to this code) is fine: expand/contract keeps old code working (homework 60)
    if current == "" or (current in KNOWN and current != HEAD):
        response.status_code = 503
        return {"status": "not_ready", "database": "migrations pending",
                "revision": current or "none", "expected": HEAD}
    return {"status": "ready", "version": settings.version, "revision": current}


@app.get("/courses")
def courses() -> list[dict]:
    return db.list_courses()


@app.get("/courses/{course_id}")
def course(course_id: int) -> dict:
    found = db.get_course(course_id)
    if found is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return found


@app.post("/courses", status_code=201)
def create_course(data: CourseIn, request: Request, response: Response) -> dict:
    created = db.add_course(data.title, data.description, data.level)
    # url_for builds an ABSOLUTE link: behind a proxy it needs X-Forwarded-Proto to be right
    response.headers["Location"] = str(request.url_for("course", course_id=created["id"]))
    return created


@app.get("/whoami")
def whoami(request: Request) -> dict[str, str | None]:
    """What the app believes about this request - behind Nginx, without/with proxy headers"""
    return {"client": request.client.host if request.client else None,
            "scheme": request.url.scheme,
            "url": str(request.url),
            "x_forwarded_for": request.headers.get("x-forwarded-for")}
