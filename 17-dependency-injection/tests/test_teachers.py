# Homework answer from Video 16
from fastapi.testclient import TestClient


def test_create_and_list_teachers(client: TestClient) -> None:
    response = client.post("/teachers", json={"name": "Nilesh", "subject": "FastAPI"})
    assert response.status_code == 201
    assert client.get("/teachers").json() == [{"id": 1, "name": "Nilesh", "subject": "FastAPI"}]


def test_teacher_404(client: TestClient) -> None:
    assert client.get("/teachers/7").json() == {"detail": "Teacher not found"}
