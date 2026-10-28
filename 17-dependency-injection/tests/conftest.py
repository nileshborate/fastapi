from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.dependencies import API_KEY
from app.main import app
from app.services import course_service, student_service, teacher_service

AUTH = {"X-API-Key": API_KEY}


@pytest.fixture
def client() -> Iterator[TestClient]:
    course_service.COURSES.clear()        # start every test with empty data
    student_service.STUDENTS.clear()
    teacher_service.TEACHERS.clear()
    yield TestClient(app)
    app.dependency_overrides.clear()      # undo any override a test made
