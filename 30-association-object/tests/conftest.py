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
def alembic_cfg() -> Config:
    return Config(str(ALEMBIC_INI))                       # the same config as the "alembic" command


@pytest.fixture
def client(alembic_cfg: Config) -> Iterator[TestClient]:
    command.downgrade(alembic_cfg, "base")                # an EMPTY database ...
    command.upgrade(alembic_cfg, "head")                  # ... built by OUR migrations - not create_all
    with TestClient(app) as test_client:
        yield test_client


def add_student(client: TestClient, name: str = "Asha") -> dict:
    return client.post("/students", json={"name": name, "email": f"{name.lower()}@example.com"}).json()


def add_course(client: TestClient, title: str = "FastAPI Basics", fee: float = 299) -> dict:
    return client.post("/courses", json={"title": title, "fee": fee}).json()


def enroll(client: TestClient, student_id: int, course_id: int):  # noqa: ANN201
    return client.post(f"/students/{student_id}/enrollments", json={"course_id": course_id})
