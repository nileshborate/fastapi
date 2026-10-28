import os

os.environ["API_KEY"] = "test-key"          # set BEFORE the app is imported: real env vars beat .env
os.environ["ENVIRONMENT"] = "test"

from collections.abc import Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import dependencies  # noqa: E402
from app.main import app  # noqa: E402
from app.services import course_service, student_service, teacher_service  # noqa: E402

TEACHER = {"X-API-Key": "test-key", "X-Role": "teacher"}
ADMIN = {"X-API-Key": "test-key", "X-Role": "admin"}


@pytest.fixture
def client() -> Iterator[TestClient]:
    course_service.COURSES.clear()        # start every test with empty data
    student_service.STUDENTS.clear()
    teacher_service.TEACHERS.clear()
    dependencies.EVENTS.clear()
    yield TestClient(app)
    app.dependency_overrides.clear()      # undo any override a test made
