import os

os.environ["API_KEY"] = "test-key"          # set BEFORE the app is imported: real env vars beat .env
os.environ["ENVIRONMENT"] = "test"
os.environ["ALLOWED_HOSTS"] = '["testserver"]'   # the TestClient calls itself "testserver"
os.environ["LOAD_SEED_DATA"] = "false"            # tests start with EMPTY data
os.environ["EMAIL_DELAY_SECONDS"] = "0"          # no waiting in tests
os.environ["LOG_FILE"] = "test-app.log"
os.environ["BACKUP_FILE"] = "test-backup.json"

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
    with TestClient(app) as test_client:   # "with" runs the lifespan: startup ... shutdown
        yield test_client
    app.dependency_overrides.clear()      # undo any override a test made
