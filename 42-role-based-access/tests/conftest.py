import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["JWT_SECRET"] = "test-secret-" + "x" * 40

from collections.abc import Iterator  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.make_admin import make_admin  # noqa: E402

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


@pytest.fixture
def client() -> Iterator[TestClient]:
    cfg = Config(str(ALEMBIC_INI))
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def auth(client: TestClient, email: str) -> dict[str, str]:
    """register (a student!), log in, and return the Authorization header"""
    client.post("/users", json={"email": email, "full_name": "Test User",
                                "password": "blue-river-42"})
    form = {"username": email, "password": "blue-river-42"}
    token = client.post("/token", data=form).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def users(client: TestClient) -> dict[str, dict[str, str]]:
    """admin Asha (id 1) · teacher Ravi (id 2) · student Meera (id 3) · a guest"""
    asha = auth(client, "asha@example.com")
    ravi = auth(client, "ravi@example.com")
    meera = auth(client, "meera@example.com")
    client.portal.call(make_admin, "asha@example.com")       # the app's event loop
    client.patch("/admin/users/2/role", json={"role": "teacher"}, headers=asha)
    return {"guest": {}, "student": meera, "teacher": ravi, "admin": asha}
