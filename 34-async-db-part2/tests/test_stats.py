# Async tests with httpx.AsyncClient: await every request
import asyncio

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import InvalidRequestError

from app.database import SessionLocal
from app.models import Course
from tests.conftest import add_school

pytestmark = pytest.mark.anyio


async def test_stats_empty(api: httpx.AsyncClient) -> None:
    response = await api.get("/stats")
    assert response.json() == {"teachers": 0, "courses": 0, "average_fee": 0.0,
                               "top_courses": []}


async def test_stats_with_gather(api: httpx.AsyncClient) -> None:
    await add_school(api)
    assert (await api.get("/stats")).json() == {
        "teachers": 1, "courses": 4, "average_fee": 424.0,
        "top_courses": ["AWS for Developers", "Docker Deep Dive", "FastAPI Basics"],
    }


async def test_courses_come_with_their_teacher(api: httpx.AsyncClient) -> None:
    await add_school(api)
    courses = (await api.get("/courses")).json()
    assert len(courses) == 4 and courses[0]["teacher"] == {"id": 1, "name": "Nilesh"}
    response = await api.post("/courses", json={"title": "Python", "fee": 1, "teacher_id": 9})
    assert response.status_code == 404


async def test_one_session_for_two_tasks_fails(api: httpx.AsyncClient) -> None:
    stmt = select(func.count()).select_from(Course)
    async with SessionLocal() as db:
        results = await asyncio.gather(db.scalar(stmt), db.scalar(stmt),
                                       return_exceptions=True)
    assert any(isinstance(r, InvalidRequestError) and "concurrent operations" in str(r)
               for r in results)


async def test_lazy_raise(api: httpx.AsyncClient) -> None:
    await add_school(api)
    async with SessionLocal() as db:
        course = await db.scalar(select(Course))
        with pytest.raises(InvalidRequestError, match="lazy='raise'"):
            course.teacher          # lazy="raise": a clear error, before any SQL is sent
