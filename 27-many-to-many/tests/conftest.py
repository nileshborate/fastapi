import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"       # tests use their OWN database file

from collections.abc import Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client() -> Iterator[TestClient]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client


def add_student(client: TestClient, name: str = "Asha") -> dict:
    return client.post("/students", json={"name": name, "email": f"{name.lower()}@example.com"}).json()


def add_course(client: TestClient, title: str = "FastAPI Basics", price: float = 299) -> dict:
    return client.post("/courses", json={"title": title, "price": price}).json()


def enroll(client: TestClient, student_id: int, course_id: int):  # noqa: ANN201
    return client.post(f"/students/{student_id}/courses/{course_id}")
