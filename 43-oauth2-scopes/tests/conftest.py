import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["JWT_SECRET"] = "test-secret-" + "x" * 40

from collections.abc import Iterator  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from alembic import command  # noqa: E402
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


def login(client: TestClient, email: str, scope: str | None = None):
    form = {"username": email, "password": "blue-river-42"}
    if scope is not None:
        form["scope"] = scope
    return client.post("/token", data=form)


def bearer(response) -> dict[str, str]:
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def users(client: TestClient) -> None:
    """Asha: admin (id 1) · Ravi: teacher (id 2) · Meera: student (id 3)"""
    for name in ("asha", "ravi", "meera"):
        client.post("/users", json={"email": f"{name}@example.com", "full_name": name.title(),
                                     "password": "blue-river-42"})
    client.portal.call(make_admin, "asha@example.com")
    asha = bearer(login(client, "asha@example.com"))
    client.patch("/admin/users/2/role", json={"role": "teacher"}, headers=asha)
