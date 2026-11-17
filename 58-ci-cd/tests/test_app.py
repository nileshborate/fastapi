# The app - CI runs these on Python 3.12 and 3.13 on every push
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setattr(get_settings(), "db_path", str(tmp_path / "test.db"))
    with TestClient(app) as test_client:
        yield test_client


def test_health(client: TestClient) -> None:
    assert client.get("/health/live").json() == {"status": "alive"}
    assert client.get("/health/ready").json() == {"status": "ready", "version": "1.6.0"}


def test_courses_are_stored(client: TestClient) -> None:
    assert client.post("/courses", json={"title": "Docker 101"}).json() == {
        "id": 1, "title": "Docker 101"}
    assert client.get("/courses").json() == [{"id": 1, "title": "Docker 101"}]


def test_not_ready_without_the_database(client: TestClient,
                                        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "db_path", "/no/such/folder/x.db")
    response = client.get("/health/ready")
    assert response.status_code == 503 and response.json()["status"] == "not_ready"


@pytest.mark.parametrize("title", ["", "Go", "x" * 81])
def test_title_must_be_3_to_80_characters(client: TestClient, title: str) -> None:
    assert client.post("/courses", json={"title": title}).status_code == 422


def test_whoami(client: TestClient) -> None:
    body = client.get("/whoami").json()
    assert set(body) == {"hostname", "user", "uid", "db_path"}
