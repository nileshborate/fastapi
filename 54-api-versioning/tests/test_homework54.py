# Homework 54: an additive change (level, v2 only) and an API-Version header
from fastapi.testclient import TestClient

V2 = {"title": "Docker 101", "teacher": {"name": "Ravi"}, "price": {"amount": "399.00"}}


def test_level_is_only_in_v2(client: TestClient) -> None:
    assert client.get("/v2/courses/1").json()["level"] == "beginner"
    assert "level" not in client.get("/v1/courses/1").json()        # v1 did not change


def test_create_with_a_level(client: TestClient) -> None:
    created = client.post("/v2/courses", json=V2 | {"level": "advanced"}).json()
    assert created["level"] == "advanced"
    assert client.post("/v2/courses", json=V2).json()["level"] == "beginner"   # optional
    assert client.post("/v2/courses", json=V2 | {"level": "expert"}).status_code == 422
    assert "level" not in client.get(f"/v1/courses/{created['id']}").json()


def test_api_version_header(client: TestClient) -> None:
    assert "title" in client.get("/courses/1", headers={"API-Version": "2"}).json()
    assert "name" in client.get("/courses/1", headers={"API-Version": "1"}).json()
    response = client.get("/courses/1", headers={"API-Version": "3"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Unknown API version: 3. Use 1 or 2."}
