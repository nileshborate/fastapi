# Homework 40: GET /me/courses/{id} (404 for somebody else's course) and PATCH /me
from fastapi.testclient import TestClient

from app.deps import get_current_active_user
from app.main import app
from app.models import User
from tests.conftest import auth


def test_my_course_is_404_for_somebody_elses(client: TestClient) -> None:
    asha, ravi = auth(client), auth(client, "ravi@example.com")
    client.post("/courses", json={"title": "FastAPI Basics", "fee": 299}, headers=asha)
    assert client.get("/me/courses/1", headers=asha).json()["title"] == "FastAPI Basics"
    response = client.get("/me/courses/1", headers=ravi)       # exists - but not Ravi's
    assert response.status_code == 404                          # NOT 403
    assert client.get("/me/courses/99", headers=asha).status_code == 404
    assert client.get("/me/courses/1").status_code == 401       # the router protects it


def test_patch_me_changes_only_my_name(client: TestClient) -> None:
    asha, ravi = auth(client), auth(client, "ravi@example.com")
    response = client.patch("/me", json={"full_name": "Asha Patil"}, headers=asha)
    assert response.status_code == 200 and response.json()["full_name"] == "Asha Patil"
    assert client.get("/me", headers=ravi).json()["full_name"] == "Test User"
    assert client.patch("/me", json={"full_name": "A"}, headers=asha).status_code == 422
    assert client.patch("/me", json={"email": "x@y.z"}, headers=asha).status_code == 422
    assert client.patch("/me", json={"full_name": "Nobody"}).status_code == 401


def test_my_course_with_an_override(client: TestClient) -> None:
    asha = auth(client)
    client.post("/courses", json={"title": "FastAPI Basics", "fee": 299}, headers=asha)
    ravi = User(id=2, email="ravi@example.com", full_name="Ravi", is_active=True)
    app.dependency_overrides[get_current_active_user] = lambda: ravi     # no token at all
    assert client.get("/me/courses/1").status_code == 404
