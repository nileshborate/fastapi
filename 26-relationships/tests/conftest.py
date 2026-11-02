import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"       # tests use their OWN database file

from collections.abc import Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client() -> Iterator[TestClient]:
    Base.metadata.drop_all(bind=engine)                    # a clean database for every test
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client


def add_teacher(client: TestClient, name: str = "Nilesh", subject: str = "FastAPI") -> dict:
    return client.post("/teachers", json={"name": name, "subject": subject}).json()


def add_course(client: TestClient, title: str, teacher_id: int, price: float = 99) -> dict:
    return client.post("/courses", json={"title": title, "price": price, "teacher_id": teacher_id}).json()
