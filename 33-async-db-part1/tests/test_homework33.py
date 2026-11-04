# Homework answer (Video 33): teacher detail, PATCH fee, awaitable_attrs in an async test
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionLocal, engine
from app.models import Course, Teacher
from tests.conftest import add_course, add_teacher


def test_teacher_with_courses(client: TestClient) -> None:
    add_teacher(client)
    add_course(client, "FastAPI Basics")
    add_course(client, "Docker Deep Dive")
    assert client.get("/teachers/1").json() == {
        "id": 1, "name": "Nilesh",
        "courses": [{"id": 1, "title": "FastAPI Basics", "fee": 299},
                    {"id": 2, "title": "Docker Deep Dive", "fee": 299}],
    }
    assert client.get("/teachers/9").status_code == 404


def test_patch_fee(client: TestClient) -> None:
    add_teacher(client)
    add_course(client)
    body = client.patch("/courses/1", json={"fee": 349}).json()
    assert body["fee"] == 349 and body["teacher"]["name"] == "Nilesh"
    assert client.get("/courses/1").json()["fee"] == 349
    assert client.patch("/courses/9", json={"fee": 1}).status_code == 404
    assert client.patch("/courses/1", json={"fee": -1}).status_code == 422


@pytest.mark.anyio
async def test_courses_with_awaitable_attrs(client: TestClient) -> None:
    # data written with an AsyncSession on THIS test's event loop (not via TestClient)
    async with SessionLocal() as db:
        db.add(Teacher(name="Nilesh", courses=[Course(title="FastAPI Basics", fee=299),
                                               Course(title="Docker Deep Dive", fee=299)]))
        await db.commit()
    async with SessionLocal() as db:
        teacher = await db.scalar(select(Teacher))
        courses = await teacher.awaitable_attrs.courses       # a query - WITH an await
        assert sorted(c.title for c in courses) == ["Docker Deep Dive", "FastAPI Basics"]
    await engine.dispose()                                    # connections of THIS loop
