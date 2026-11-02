from fastapi.testclient import TestClient

from tests.conftest import add_course, add_student


def test_create_student_and_course(client: TestClient) -> None:
    assert add_student(client) == {"id": 1, "name": "Asha", "email": "asha@example.com"}
    assert add_course(client) == {"id": 1, "title": "FastAPI Basics", "price": 299.0}


def test_duplicates_are_409(client: TestClient) -> None:
    add_student(client)
    add_course(client)
    assert client.post("/students", json={"name": "Asha", "email": "asha@example.com"}).status_code == 409
    assert client.post("/courses", json={"title": "FastAPI Basics", "price": 1}).status_code == 409


def test_new_objects_have_empty_lists(client: TestClient) -> None:
    add_student(client)
    add_course(client)
    assert client.get("/students/1").json()["courses"] == []
    assert client.get("/courses/1").json()["students"] == []


def test_404s(client: TestClient) -> None:
    assert client.get("/students/9").json() == {"detail": "Student not found"}
    assert client.get("/courses/9").json() == {"detail": "Course not found"}
