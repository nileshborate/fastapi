# Testing ONE role without passwords or tokens: override the user dependency
from fastapi.testclient import TestClient

from app.deps import get_current_active_user
from app.main import app
from app.models import User


def test_a_fake_admin(client: TestClient) -> None:
    admin = User(id=1, email="boss@example.com", full_name="Boss", role="admin", is_active=True)
    app.dependency_overrides[get_current_active_user] = lambda: admin
    assert client.get("/admin/users").status_code == 200          # no token at all


def test_a_fake_student(client: TestClient) -> None:
    student = User(id=7, email="kid@example.com", full_name="Kid", role="student",
                   is_active=True)
    app.dependency_overrides[get_current_active_user] = lambda: student
    assert client.get("/admin/users").status_code == 403
    assert client.post("/courses", json={"title": "Hacking 101", "fee": 1}).status_code == 403
