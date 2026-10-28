# Run from the project folder:  pytest -v
from fastapi.testclient import TestClient

from app.dependencies import require_admin
from app.main import app
from tests.conftest import ADMIN, TEACHER


def add_courses(client: TestClient, n: int) -> None:
    for i in range(1, n + 1):
        client.post("/courses", json={"title": f"Course {i}", "price": 100 * i}, headers=TEACHER)


def test_pagination_class(client: TestClient) -> None:
    add_courses(client, 12)
    assert len(client.get("/courses").json()) == 10
    assert [c["id"] for c in client.get("/courses", params={"skip": 10, "limit": 5}).json()] == [11, 12]
    assert client.get("/courses", params={"limit": 500}).status_code == 422


def test_create_needs_staff_role(client: TestClient) -> None:
    body = {"title": "FastAPI Basics", "price": 499}
    student = {"X-API-Key": TEACHER["X-API-Key"]}                    # no X-Role -> "student"
    assert client.post("/courses", json=body, headers=student).status_code == 403
    assert client.post("/courses", json=body, headers=TEACHER).status_code == 201


def test_delete_needs_admin(client: TestClient) -> None:
    add_courses(client, 1)
    assert client.delete("/courses/1", headers=TEACHER).json() == {"detail": "Admins only"}
    assert client.delete("/courses/1", headers=ADMIN).status_code == 204


def test_override_require_admin(client: TestClient) -> None:              # homework answer (Video 17)
    add_courses(client, 1)
    app.dependency_overrides[require_admin] = lambda: None
    assert client.delete("/courses/1", headers=TEACHER).status_code == 204


def test_course_filter(client: TestClient) -> None:                       # homework answer (Video 18)
    add_courses(client, 5)                                                # prices 100 ... 500
    response = client.get("/courses", params={"min_price": 200, "max_price": 400})
    assert [c["price"] for c in response.json()] == [200.0, 300.0, 400.0]
