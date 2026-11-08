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

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"
ASHA = {"email": "asha@example.com", "full_name": "Asha Patil", "password": "blue-river-42"}


@pytest.fixture
def client() -> Iterator[TestClient]:
    cfg = Config(str(ALEMBIC_INI))
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    with TestClient(app) as test_client:
        test_client.post("/users", json=ASHA)
        yield test_client


def get_token(client: TestClient, username: str = "asha@example.com",
              password: str = "blue-river-42") -> str:
    form = {"username": username, "password": password}
    return client.post("/token", data=form).json()["access_token"]
