# The async API - tested with the SAME TestClient as before
from fastapi.testclient import TestClient
from sqlalchemy import event

from app.database import engine
from tests.conftest import add_course, add_teacher


def test_health_shows_the_async_driver(client: TestClient) -> None:
    assert client.get("/").json()["driver"] in ("aiosqlite", "asyncpg")


def test_create_and_list(client: TestClient) -> None:
    add_teacher(client)
    response = add_course(client)
    assert response.status_code == 201
    assert response.json() == {"id": 1, "title": "FastAPI Basics", "fee": 299,
                               "teacher": {"id": 1, "name": "Nilesh"}}
    add_course(client, "Docker Deep Dive")
    assert [c["title"] for c in client.get("/courses").json()] == ["FastAPI Basics",
                                                                   "Docker Deep Dive"]


def test_errors(client: TestClient) -> None:
    add_teacher(client)
    assert add_course(client, teacher_id=9).json() == {"detail": "Teacher not found"}
    add_course(client)
    assert add_course(client).status_code == 409
    assert client.get("/courses/9").status_code == 404


def test_list_needs_two_queries(client: TestClient) -> None:
    add_teacher(client)
    for k in range(5):
        add_course(client, f"Course number {k}")
    queries: list[str] = []
    listener = lambda *args: queries.append(args[2])  # noqa: E731
    event.listen(engine.sync_engine, "before_cursor_execute", listener)   # the sync core inside
    try:
        assert len(client.get("/courses").json()) == 5
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", listener)
    selects = [q for q in queries if q.lstrip().startswith("SELECT")]
    assert len(selects) == 2                    # courses + teachers (selectinload)
