# Video 56 - health checks and metrics: /health/live · /health/ready · /metrics
# fastapi dev app/main.py
import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app import db, health
from app.config import get_settings
from app.metrics import APP_INFO, ENROLLMENTS, MetricsMiddleware, metrics_endpoint


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    db.init_db()
    APP_INFO.labels(get_settings().version).set(1)  # homework 56: the label is the info
    app.state.shutting_down = False
    yield
    app.state.shutting_down = True                  # readiness says 503 while we drain
    await health.http.aclose()


app = FastAPI(title="Course Hub - health and metrics", lifespan=lifespan)
app.add_middleware(MetricsMiddleware)
app.include_router(health.router)
app.add_api_route("/metrics", metrics_endpoint, include_in_schema=False)


@app.get("/courses")
def courses() -> list[dict[str, object]]:
    return db.list_courses()


@app.post("/enrollments/{course_id}", status_code=201)
def enroll(course_id: int) -> dict[str, int]:
    if course_id not in {c[0] for c in db.COURSES}:
        raise HTTPException(status_code=404, detail="Course not found")
    ENROLLMENTS.labels(str(course_id)).inc()
    return {"course_id": course_id}


@app.get("/reports/{course_id}")
async def report(course_id: int) -> dict[str, int]:
    await asyncio.sleep(0.1 * course_id)            # course 3 takes ~300 ms
    return {"course_id": course_id}


@app.get("/boom")
def boom() -> dict[str, float]:
    return {"average": 100 / 0}                     # a real bug -> 500
