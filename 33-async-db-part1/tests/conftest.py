import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"   # an ASYNC URL for the tests too

from collections.abc import Iterator  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


@pytest.fixture
def client() -> Iterator[TestClient]:
    cfg = Config(str(ALEMBIC_INI))
    command.downgrade(cfg, "base")                    # env.py runs the async migrations
    command.upgrade(cfg, "head")
    with TestClient(app) as test_client:              # works with async def endpoints too
        yield test_client


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"                                  # async tests run on asyncio


def add_teacher(client: TestClient, name: str = "Nilesh") -> dict:
    return client.post("/teachers", json={"name": name}).json()


def add_course(client: TestClient, title: str = "FastAPI Basics", teacher_id: int = 1):  # noqa
    return client.post("/courses", json={"title": title, "fee": 299, "teacher_id": teacher_id})
