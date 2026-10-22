# Run:  pytest -v
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_get_course() -> None:
    response = client.get("/courses/2")
    assert response.status_code == 200
    assert response.json()["title"] == "Pydantic Models"


def test_course_not_found() -> None:
    response = client.get("/courses/99")
    assert response.status_code == 404
    assert response.json() == {"detail": "Course not found"}


def test_course_id_must_be_int() -> None:
    assert client.get("/courses/abc").status_code == 422


def test_course_id_must_be_positive() -> None:
    assert client.get("/courses/0").status_code == 422


def test_latest_route_order() -> None:
    assert client.get("/courses/latest").json()["id"] == 3


def test_level_enum() -> None:
    assert len(client.get("/levels/beginner").json()) == 2
    assert client.get("/levels/expert").status_code == 422


def test_multiple_params() -> None:
    assert client.get("/students/7/courses/2").json() == {"student_id": 7, "course_id": 2}


def test_path_converter() -> None:
    assert client.get("/files/notes/week1/intro.txt").json() == {"file_path": "notes/week1/intro.txt"}
