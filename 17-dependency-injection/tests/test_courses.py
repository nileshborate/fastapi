# Run from the project folder:  pytest -v
from fastapi.testclient import TestClient

from app.dependencies import verify_api_key
from app.main import app
from tests.conftest import AUTH


def add_courses(client: TestClient, n: int) -> None:
    for i in range(1, n + 1):
        client.post("/courses", json={"title": f"Course {i}", "price": 100 * i}, headers=AUTH)


def test_pagination_defaults_and_values(client: TestClient) -> None:
    add_courses(client, 12)
    assert len(client.get("/courses").json()) == 10                       # default limit
    page = client.get("/courses", params={"skip": 10, "limit": 5}).json()
    assert [c["id"] for c in page] == [11, 12]


def test_pagination_validation(client: TestClient) -> None:
    assert client.get("/courses", params={"limit": 500}).status_code == 422


def test_api_key_required(client: TestClient) -> None:
    body = {"title": "FastAPI Basics", "price": 499}
    assert client.post("/courses", json=body).status_code == 422                      # header missing
    assert client.post("/courses", json=body, headers={"X-API-Key": "nope"}).status_code == 401
    assert client.post("/courses", json=body, headers=AUTH).status_code == 201


def test_get_course_or_404(client: TestClient) -> None:
    add_courses(client, 1)
    assert client.get("/courses/1").json()["title"] == "Course 1"
    assert client.get("/courses/9").json() == {"detail": "Course not found"}


def test_delete_uses_both_dependencies(client: TestClient) -> None:
    add_courses(client, 1)
    assert client.delete("/courses/1").status_code == 422                 # no key
    assert client.delete("/courses/9", headers=AUTH).status_code == 404   # key ok, no course
    assert client.delete("/courses/1", headers=AUTH).status_code == 204


def test_override_dependency(client: TestClient) -> None:
    app.dependency_overrides[verify_api_key] = lambda: None               # skip the key check
    response = client.post("/courses", json={"title": "No key needed", "price": 0})
    assert response.status_code == 201
