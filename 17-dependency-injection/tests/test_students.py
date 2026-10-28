from fastapi.testclient import TestClient

from tests.conftest import AUTH


def test_create_and_get_student(client: TestClient) -> None:
    response = client.post("/students", json={"name": "Asha", "email": "asha@example.com"}, headers=AUTH)
    assert response.status_code == 201
    assert client.get("/students/1").json() == {"id": 1, "name": "Asha", "email": "asha@example.com"}


def test_students_pagination(client: TestClient) -> None:
    for name in ["Asha", "Ravi", "Meera"]:
        client.post("/students", json={"name": name, "email": f"{name.lower()}@example.com"}, headers=AUTH)
    assert [s["name"] for s in client.get("/students", params={"skip": 1, "limit": 1}).json()] == ["Ravi"]
