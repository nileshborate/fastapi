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

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"
PASSWORD = "blue-river-42"


@pytest.fixture
def client() -> Iterator[TestClient]:
    cfg = Config(str(ALEMBIC_INI))
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    for limiter in ("login_limiter", "write_limiter", "ip_limiter", "domain_limiter"):
        getattr(app.state, limiter).reset()              # every test starts with 0 hits
    with TestClient(app) as test_client:
        yield test_client


def auth(client: TestClient, email: str = "asha@example.com") -> dict[str, str]:
    client.post("/users", json={"email": email, "full_name": "Test User", "password": PASSWORD})
    token = client.post("/token", data={"username": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {token.json()['access_token']}"}
