from fastapi.testclient import TestClient


def test_create_and_get_student(client: TestClient) -> None:
    response = client.post("/students", json={"name": "Asha", "email": "asha@example.com"})
    assert response.status_code == 201
    assert client.get("/students/1").json() == {"id": 1, "name": "Asha", "email": "asha@example.com"}


def test_student_validation(client: TestClient) -> None:
    assert client.post("/students", json={"name": "A", "email": "wrong"}).status_code == 422


def test_student_404(client: TestClient) -> None:
    assert client.get("/students/5").json() == {"detail": "Student not found"}
