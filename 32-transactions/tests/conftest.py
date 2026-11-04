import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"       # tests use their OWN database file

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
    command.downgrade(cfg, "base")                        # an EMPTY database ...
    command.upgrade(cfg, "head")                          # ... built by our migrations
    with TestClient(app) as test_client:
        yield test_client


def add_student(client: TestClient, name: str = "Asha", balance: int = 500) -> dict:
    return client.post("/students", json={"name": name, "balance": balance}).json()


def add_course(client: TestClient, seats: int = 2, fee: int = 299) -> dict:
    return client.post("/courses", json={"title": "FastAPI Basics", "fee": fee,
                                         "seats_left": seats}).json()


def enroll(client: TestClient, student_id: int, course_id: int = 1):  # noqa: ANN201
    return client.post("/enrollments", json={"student_id": student_id, "course_id": course_id})
