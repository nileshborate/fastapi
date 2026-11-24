# Course Hub on PostgreSQL - every test runs against the real database
import psycopg
import pytest
from fastapi.testclient import TestClient

from app import main
from app.db import Database

NOBODY = "postgresql://nobody:x@127.0.0.1:1/none"     # port 1: nothing listens there


def test_health(client: TestClient) -> None:
    assert client.get("/health/live").json() == {"status": "alive"}
    assert client.get("/health/ready").json() == {"status": "ready", "version": "1.7.0"}


def test_courses_are_stored(client: TestClient) -> None:
    assert client.post("/courses", json={"title": "Docker 101"}).json() == {
        "id": 1, "title": "Docker 101", "description": None}
    client.post("/courses", json={"title": "PostgreSQL 101"})
    titles = [c["title"] for c in client.get("/courses").json()]
    assert titles == ["Docker 101", "PostgreSQL 101"]


@pytest.mark.parametrize("title", ["", "Go", "x" * 81])
def test_title_must_be_3_to_80_characters(client: TestClient, title: str) -> None:
    assert client.post("/courses", json={"title": title}).status_code == 422


def test_the_database_checks_the_title_too(client: TestClient) -> None:
    with pytest.raises(psycopg.errors.CheckViolation):          # the last line of defence
        main.db.add_course("Go")


def test_a_parameter_is_never_sql(client: TestClient) -> None:
    evil = "x'); DROP TABLE courses; --"
    assert client.post("/courses", json={"title": evil}).json()["title"] == evil
    courses = client.get("/courses").json()                      # the table is still there
    assert courses == [{"id": 1, "title": evil, "description": None}]


def test_not_ready_without_the_database(client: TestClient,
                                        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "db", Database(NOBODY))
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "database": "unreachable"}


def test_no_database_no_start() -> None:
    with pytest.raises(psycopg.OperationalError):              # PoolTimeout after 1 s
        Database(NOBODY).open(wait_s=1)
