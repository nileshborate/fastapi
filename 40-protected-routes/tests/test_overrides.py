# dependency_overrides: test a protected route WITHOUT logging in
from fastapi.testclient import TestClient

from app.deps import get_current_active_user
from app.main import app
from app.models import User


def test_override_the_current_user(client: TestClient) -> None:
    client.post("/users", json={"email": "asha@example.com", "full_name": "Asha Patil",
                                "password": "blue-river-42"})
    fake = User(id=1, email="asha@example.com", full_name="Asha Patil", is_active=True)
    app.dependency_overrides[get_current_active_user] = lambda: fake    # no token needed
    response = client.post("/courses", json={"title": "FastAPI Basics", "fee": 299})
    assert response.status_code == 201 and response.json()["owner_id"] == 1
    assert client.get("/me").json()["full_name"] == "Asha Patil"
