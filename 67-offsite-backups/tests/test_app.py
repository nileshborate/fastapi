# Course Hub 1.16.0 - the api (behind Nginx in production)
import psycopg
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from app import main
from app.db import Database

NOBODY = "postgresql://nobody:x@127.0.0.1:1/none"     # port 1: nothing listens there


def test_ready_at_head(client: TestClient) -> None:
    assert client.get("/health/live").json() == {"status": "alive"}
    assert client.get("/health/ready").json() == {
        "status": "ready", "version": "1.16.0", "revision": "0005", "commit": "dev"}


def test_ready_names_the_commit(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    sha = "f5166fc1228ffdbc71e0c5604962e63bd8c4536b"          # GIT_SHA, set by the build
    monkeypatch.setattr(main.settings, "git_sha", sha)
    assert client.get("/health/ready").json()["commit"] == "f5166fc1228f"   # 12 characters


def test_courses_get_a_level(client: TestClient) -> None:
    assert client.post("/courses", json={"title": "Docker 101"}).json() == {
        "id": 1, "title": "Docker 101", "description": None, "level": "beginner"}
    body = {"title": "Alembic", "description": "In production", "level": "advanced"}
    assert client.post("/courses", json=body).json() == {"id": 2, **body}
    assert [c["level"] for c in client.get("/courses").json()] == ["beginner", "advanced"]


@pytest.mark.parametrize("body", [{"title": "Go"}, {"title": "Docker", "level": "expert"}])
def test_bad_input_is_422(client: TestClient, body: dict) -> None:
    assert client.post("/courses", json=body).status_code == 422


def test_the_database_checks_the_level_too(client: TestClient) -> None:
    with pytest.raises(psycopg.errors.CheckViolation):          # courses_level_check (0002)
        main.db.add_course("Docker", None, "expert")


def test_not_ready_while_migrations_are_pending(client: TestClient, cfg: Config) -> None:
    command.downgrade(cfg, "0004")                      # the NEW code on an OLD schema
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "database": "migrations pending",
                               "revision": "0004", "expected": "0005"}
    command.upgrade(cfg, "head")
    assert client.get("/health/ready").status_code == 200


def test_not_ready_without_the_database(client: TestClient,
                                        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "db", Database(NOBODY))
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "database": "unreachable"}


def test_no_database_no_start() -> None:
    with pytest.raises(psycopg.OperationalError):              # PoolTimeout after 1 s
        Database(NOBODY).open(wait_s=1)


def test_one_course_and_its_location(client: TestClient) -> None:
    response = client.post("/courses", json={"title": "Nginx + HTTPS"})
    assert response.headers["location"] == "http://testserver/courses/1"    # no proxy: http
    assert client.get("/courses/1").json()["title"] == "Nginx + HTTPS"
    assert client.get("/courses/2").status_code == 404


def test_courses_is_a_page_now(client: TestClient) -> None:      # Video 66
    for k in range(3):
        client.post("/courses", json={"title": f"Course {k}"})
    first = client.get("/courses?limit=2").json()
    assert [c["title"] for c in first] == ["Course 0", "Course 1"]
    second = client.get("/courses?limit=2&offset=2").json()
    assert [c["title"] for c in second] == ["Course 2"]
    assert client.get("/courses?limit=201").status_code == 422      # at most 200 at once
