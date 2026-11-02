from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.services import course_service


def test_startup_sets_the_start_time(client: TestClient) -> None:
    body = client.get("/").json()
    assert body["uptime_seconds"] >= 0                  # app.state.started_at was set at startup


def test_lifespan_loads_and_clears_courses(monkeypatch: pytest.MonkeyPatch) -> None:
    course_service.COURSES.clear()
    monkeypatch.setenv("LOAD_SEED_DATA", "true")
    get_settings.cache_clear()                          # read the environment again
    try:
        with TestClient(app) as client:                 # STARTUP runs here
            titles = [c["title"] for c in client.get("/courses").json()]
            assert titles == ["FastAPI Basics", "Pydantic Models", "Async Python"]
        assert course_service.COURSES == {}             # SHUTDOWN ran when the "with" ended
    finally:
        get_settings.cache_clear()


def test_load_courses(tmp_path: Path) -> None:
    course_service.COURSES.clear()
    seed = tmp_path / "courses.json"
    seed.write_text('[{"title": "Docker Basics", "price": 99}]')
    assert course_service.load_courses(seed) == 1
    assert course_service.COURSES[1].title == "Docker Basics"
    course_service.COURSES.clear()
