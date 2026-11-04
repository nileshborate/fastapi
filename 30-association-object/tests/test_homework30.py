# Homework answer (Video 30): enrollment status, ?status= on the roster, completed_count
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import engine
from tests.conftest import add_course, add_student, enroll


def test_new_enrollment_is_active(client: TestClient) -> None:
    add_student(client)
    add_course(client)
    assert enroll(client, 1, 1).json()["status"] == "active"


def test_patch_status_and_grade(client: TestClient) -> None:
    add_student(client)
    add_course(client)
    enroll(client, 1, 1)
    body = client.patch("/students/1/enrollments/1", json={"status": "completed"}).json()
    assert (body["status"], body["grade"]) == ("completed", None)
    body = client.patch("/students/1/enrollments/1", json={"grade": 88}).json()
    assert (body["status"], body["grade"]) == ("completed", 88)          # status kept
    assert client.patch("/students/1/enrollments/1", json={"status": "paused"}).status_code == 422


def test_roster_filter_and_completed_count(client: TestClient) -> None:
    for name in ("Asha", "Ravi", "Meera"):
        add_student(client, name)
    add_course(client)
    for student_id in (1, 2, 3):
        enroll(client, student_id, 1)
    client.patch("/students/1/enrollments/1", json={"status": "completed"})
    client.patch("/students/3/enrollments/1", json={"status": "dropped"})
    course = client.get("/courses/1", params={"status": "active"}).json()
    assert [r["student"]["name"] for r in course["enrollments"]] == ["Ravi"]
    assert course["completed_count"] == 1
    assert len(client.get("/courses/1").json()["enrollments"]) == 3     # no filter: everyone
    assert client.get("/courses/1", params={"status": "paused"}).status_code == 422


def test_old_enrollments_become_active(client: TestClient, alembic_cfg: Config) -> None:
    command.downgrade(alembic_cfg, "0002")                              # no status column yet
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO students (name, email) VALUES ('Asha', 'asha@example.com')"))
        conn.execute(text("INSERT INTO courses (title, fee) VALUES ('FastAPI Basics', 299)"))
        conn.execute(text("INSERT INTO enrollments (student_id, course_id) VALUES (1, 1)"))
    command.upgrade(alembic_cfg, "head")
    assert client.get("/students/1").json()["enrollments"][0]["status"] == "active"
