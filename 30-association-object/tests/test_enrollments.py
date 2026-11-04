# The association object through the API: enroll, grade, the two "detail" views, unenroll
from fastapi.testclient import TestClient
from sqlalchemy import event, func, select

from app.database import SessionLocal, engine
from app.models import Enrollment
from tests.conftest import add_course, add_student, enroll


def test_enroll_returns_the_link_data(client: TestClient) -> None:
    add_student(client)
    add_course(client)
    response = enroll(client, 1, 1)
    assert response.status_code == 201
    body = response.json()
    assert body["course"]["title"] == "FastAPI Basics"
    assert body["enrolled_at"] is not None                 # filled by the DATABASE (server_default)
    assert body["grade"] is None


def test_enroll_errors(client: TestClient) -> None:
    add_student(client)
    add_course(client)
    enroll(client, 1, 1)
    assert enroll(client, 1, 1).json() == {"detail": "Already enrolled"}
    assert enroll(client, 1, 99).json() == {"detail": "Course not found"}
    assert enroll(client, 99, 1).json() == {"detail": "Student not found"}


def test_set_grade_and_average(client: TestClient) -> None:
    add_student(client, "Asha")
    add_student(client, "Ravi")
    add_course(client)
    enroll(client, 1, 1)
    enroll(client, 2, 1)
    response = client.patch("/students/1/enrollments/1", json={"grade": 92})
    assert response.status_code == 200
    assert response.json()["grade"] == 92
    assert response.json()["course"]["average_grade"] == 92.0     # Ravi has no grade: NULL is ignored
    client.patch("/students/2/enrollments/1", json={"grade": 78})
    assert client.get("/courses/1").json()["average_grade"] == 85.0


def test_grade_errors(client: TestClient) -> None:
    add_student(client)
    add_course(client)
    enroll(client, 1, 1)
    assert client.patch("/students/1/enrollments/1", json={"grade": 120}).status_code == 422
    assert client.patch("/students/1/enrollments/2", json={"grade": 50}).json() == {"detail": "Enrollment not found"}


def test_student_detail(client: TestClient) -> None:
    add_student(client)
    add_course(client, "FastAPI Basics")
    add_course(client, "Docker Deep Dive", 499)
    enroll(client, 1, 2)
    enroll(client, 1, 1)
    client.patch("/students/1/enrollments/1", json={"grade": 92})
    rows = client.get("/students/1").json()["enrollments"]
    assert [(r["course"]["title"], r["grade"]) for r in rows] == [("FastAPI Basics", 92), ("Docker Deep Dive", None)]


def test_course_roster(client: TestClient) -> None:
    add_student(client, "Asha")
    add_student(client, "Ravi")
    add_course(client)
    enroll(client, 2, 1)
    enroll(client, 1, 1)
    roster = client.get("/courses/1").json()["enrollments"]
    assert [r["student"]["name"] for r in roster] == ["Asha", "Ravi"]


def test_association_proxy(client: TestClient) -> None:
    add_student(client)
    add_course(client, "FastAPI Basics")
    add_course(client, "Docker Deep Dive", 499)
    enroll(client, 1, 1)
    enroll(client, 1, 2)
    assert [c["title"] for c in client.get("/students/1/courses").json()] == ["FastAPI Basics", "Docker Deep Dive"]


def test_unenroll(client: TestClient) -> None:
    add_student(client)
    add_course(client)
    enroll(client, 1, 1)
    assert client.delete("/students/1/enrollments/1").status_code == 204
    assert client.delete("/students/1/enrollments/1").status_code == 404
    assert client.get("/students/1").json()["enrollments"] == []


def test_delete_student_deletes_the_enrollments(client: TestClient) -> None:
    add_student(client)
    add_course(client)
    enroll(client, 1, 1)
    assert client.delete("/students/1").status_code == 204
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Enrollment)) == 0
    assert client.get("/courses/1").status_code == 200              # the course stays


def test_student_detail_needs_3_queries(client: TestClient) -> None:
    add_student(client)
    for k in range(5):
        add_course(client, f"Course number {k}")
        enroll(client, 1, k + 1)
    queries: list[str] = []
    listener = lambda *args: queries.append(args[2])  # noqa: E731
    event.listen(engine, "before_cursor_execute", listener)
    try:
        assert len(client.get("/students/1").json()["enrollments"]) == 5
    finally:
        event.remove(engine, "before_cursor_execute", listener)
    assert len([q for q in queries if q.lstrip().startswith("SELECT")]) == 3   # student · enrollments · courses
