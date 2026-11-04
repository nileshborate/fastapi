from fastapi.testclient import TestClient


def test_create_and_list(client: TestClient) -> None:
    response = client.post("/courses", json={"title": "FastAPI Basics", "price": 299})
    assert response.status_code == 201
    assert response.json() == {"id": 1, "title": "FastAPI Basics", "price": 299.0, "level": "beginner"}
    client.post("/courses", json={"title": "Docker Deep Dive", "price": 499, "level": "advanced"})
    assert [c["level"] for c in client.get("/courses").json()] == ["beginner", "advanced"]


def test_unknown_level_is_422(client: TestClient) -> None:
    assert client.post("/courses", json={"title": "FastAPI Basics", "price": 1, "level": "expert"}).status_code == 422


def test_duplicate_title_is_409(client: TestClient) -> None:
    client.post("/courses", json={"title": "FastAPI Basics", "price": 299})
    assert client.post("/courses", json={"title": "FastAPI Basics", "price": 1}).status_code == 409
