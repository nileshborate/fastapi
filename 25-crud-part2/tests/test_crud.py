from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.errors import NotFoundError
from app.services import course_service
from tests.conftest import ADMIN, TEACHER

ASHA = {"name": "Asha", "email": "asha@example.com"}
MEERA = {"name": "Meera", "email": "meera@example.com", "subject": "Python"}


# ---------------------------------------------------------------- schemas in depth
def test_create_rejects_unknown_fields(client: TestClient) -> None:
    body = {"title": "Docker Basics", "price": 99, "id": 500}           # the client tries to choose the id
    response = client.post("/courses", json=body, headers=TEACHER)
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "extra_forbidden"


def test_out_has_the_database_fields(client: TestClient) -> None:
    body = client.post("/courses", json={"title": "Docker Basics", "price": 99}, headers=TEACHER).json()
    assert body["id"] == 1
    assert datetime.fromisoformat(body["created_at"])                  # filled by the DATABASE


# ---------------------------------------------------------------- 409 Conflict (homework answer, Video 23)
def test_duplicate_title_is_409(client: TestClient) -> None:
    course = {"title": "Docker Basics", "price": 99}
    assert client.post("/courses", json=course, headers=TEACHER).status_code == 201
    response = client.post("/courses", json=course, headers=TEACHER)
    assert response.status_code == 409
    assert response.json() == {"detail": "Course title already exists"}
    second = {"title": "Docker Advanced", "price": 199}                # after rollback, the app still works
    assert client.post("/courses", json=second, headers=TEACHER).status_code == 201


# ---------------------------------------------------------------- students in the database (homework, Video 23)
def test_student_by_email(client: TestClient) -> None:
    client.post("/students", json=ASHA, headers=TEACHER)
    assert client.get("/students/by-email/asha@example.com").json()["name"] == "Asha"
    assert client.get("/students/by-email/nobody@example.com").json() == {"detail": "Student not found"}


def test_duplicate_email_is_409(client: TestClient) -> None:
    client.post("/students", json=ASHA, headers=TEACHER)
    response = client.post("/students", json=ASHA, headers=TEACHER)
    assert response.status_code == 409
    assert response.json() == {"detail": "Email already registered"}


def test_admin_db(client: TestClient) -> None:                          # homework answer (Video 23)
    body = client.get("/admin/db", headers=ADMIN).json()
    assert body == {"database": "sqlite", "tables": ["courses", "students", "teachers"]}


# ---------------------------------------------------------------- teachers in the database
def test_teachers_are_saved(client: TestClient) -> None:
    created = client.post("/teachers", json=MEERA, headers=TEACHER).json()
    assert client.get(f"/teachers/{created['id']}", headers=TEACHER).json() == created


# ---------------------------------------------------------------- domain errors
def test_the_service_raises_not_found(client: TestClient) -> None:
    with SessionLocal() as db, pytest.raises(NotFoundError, match="Course not found"):
        course_service.get_course(db, 99)


def test_not_found_becomes_404(client: TestClient) -> None:
    assert client.get("/courses/99").json() == {"detail": "Course not found"}
    assert client.get("/teachers/99", headers=TEACHER).json() == {"detail": "Teacher not found"}
