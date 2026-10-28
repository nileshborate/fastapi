from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import course_service, student_service


@pytest.fixture
def client() -> Iterator[TestClient]:
    course_service.COURSES.clear()        # start every test with empty data
    student_service.STUDENTS.clear()
    yield TestClient(app)
