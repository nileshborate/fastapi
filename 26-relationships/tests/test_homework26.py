# Homework answer (Video 26) - shown at the start of Video 27
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.database import engine
from tests.conftest import add_course, add_teacher


def count_selects(client: TestClient, url: str) -> tuple[Any, int]:
    selects: list[str] = []

    def count(conn: Any, cursor: Any, statement: str, *args: Any) -> None:
        if statement.startswith("SELECT"): selects.append(statement)

    event.listen(engine, "before_cursor_execute", count)
    try:
        body = client.get(url).json()
    finally:
        event.remove(engine, "before_cursor_execute", count)
    return body, len(selects)


def test_patch_moves_a_course_to_another_teacher(client: TestClient) -> None:
    nilesh, priya = add_teacher(client), add_teacher(client, "Priya", "Python")
    course = add_course(client, "FastAPI Basics", nilesh["id"])
    body = client.patch(f"/courses/{course['id']}", json={"teacher_id": priya["id"]}).json()
    assert body["teacher"] == {"id": priya["id"], "name": "Priya"}


def test_patch_unknown_teacher_is_404(client: TestClient) -> None:
    course = add_course(client, "FastAPI Basics", add_teacher(client)["id"])
    response = client.patch(f"/courses/{course['id']}", json={"teacher_id": 42})
    assert response.status_code == 404
    assert response.json() == {"detail": "Teacher not found"}


def test_teachers_with_courses_in_two_queries(client: TestClient) -> None:
    for i in range(3):
        teacher = add_teacher(client, f"Teacher {i}")
        add_course(client, f"Course {i}a", teacher["id"])
        add_course(client, f"Course {i}b", teacher["id"])
    body, selects = count_selects(client, "/teachers?with_courses=true")
    assert [len(t["courses"]) for t in body] == [2, 2, 2]
    assert selects == 2                                    # teachers + all their courses


def test_teachers_without_courses_in_one_query(client: TestClient) -> None:
    add_course(client, "FastAPI Basics", add_teacher(client)["id"])
    body, selects = count_selects(client, "/teachers")
    assert "courses" not in body[0]
    assert selects == 1


def test_course_count(client: TestClient) -> None:
    nilesh = add_teacher(client)
    assert nilesh["course_count"] == 0
    add_course(client, "FastAPI Basics", nilesh["id"])
    add_course(client, "Async Python", nilesh["id"])
    assert client.get("/teachers").json()[0]["course_count"] == 2
