from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.main import app
from app.services import course_service


@pytest.fixture
def empty_db() -> Iterator[None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    get_settings.cache_clear()                          # tests below change the environment


def test_startup_sets_the_start_time(client: TestClient) -> None:
    body = client.get("/").json()
    assert body["uptime_seconds"] >= 0                  # app.state.started_at was set at startup
    assert body["database"] == "sqlite"


def test_lifespan_loads_the_seed_only_once(empty_db: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOAD_SEED_DATA", "true")
    get_settings.cache_clear()                          # read the environment again
    with TestClient(app) as client:                     # STARTUP: tables + 3 courses
        titles = [c["title"] for c in client.get("/courses").json()]
        assert titles == ["FastAPI Basics", "Pydantic Models", "Async Python"]
    with TestClient(app) as client:                     # a "restart": the data is still there
        assert len(client.get("/courses").json()) == 3  # ... and NOT loaded twice


def test_load_courses_only_into_an_empty_table(empty_db: None, tmp_path: Path) -> None:
    seed = tmp_path / "courses.json"
    seed.write_text('[{"title": "Docker Basics", "price": 99}]')
    with SessionLocal() as db:
        assert course_service.load_courses(db, seed) == 1
        assert course_service.load_courses(db, seed) == 0           # not empty any more
        assert course_service.count_courses(db) == 1


# ---------------------------------------------------------------- homework answer (Video 21)
def test_missing_seed_file_does_not_crash(
    empty_db: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("LOAD_SEED_DATA", "true")
    monkeypatch.setenv("SEED_FILE", str(tmp_path / "missing.json"))
    get_settings.cache_clear()
    with TestClient(app) as client:
        assert client.get("/courses").json() == []      # started, with empty data
    assert "not found - starting with empty data" in capsys.readouterr().out
