# Video 57 - FastAPI in Docker: the same app, now in a small, safe image
import getpass
import os
import socket
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from pydantic import BaseModel

from app import db
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    db.init_db()
    yield


app = FastAPI(title="Course Hub in Docker", lifespan=lifespan)


class CourseIn(BaseModel):
    title: str


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/health/ready")
def ready(response: Response) -> dict[str, str]:
    try:
        with db.connect() as conn:
            conn.execute("SELECT 1")
    except Exception as exc:
        response.status_code = 503
        return {"status": "not_ready", "error": str(exc)}
    return {"status": "ready", "version": get_settings().version}


@app.get("/whoami")
def whoami() -> dict[str, object]:
    """where am I running? - the container id is the hostname"""
    return {"hostname": socket.gethostname(), "user": getpass.getuser(), "uid": os.getuid(),
            "db_path": get_settings().db_path}


@app.get("/courses")
def courses() -> list[dict[str, object]]:
    return db.list_courses()


@app.post("/courses", status_code=201)
def create_course(data: CourseIn) -> dict[str, object]:
    return {"id": db.add_course(data.title), "title": data.title}
