from fastapi.testclient import TestClient

from tests.conftest import TEACHER


def test_create_and_get_student(client: TestClient) -> None:
    client.post("/students", json={"name": "Asha", "email": "asha@example.com"}, headers=TEACHER)
    assert client.get("/students/1").json() == {"id": 1, "name": "Asha", "email": "asha@example.com"}


def test_student_dep_404(client: TestClient) -> None:                     # homework answer (Video 17)
    assert client.get("/students/5").json() == {"detail": "Student not found"}
