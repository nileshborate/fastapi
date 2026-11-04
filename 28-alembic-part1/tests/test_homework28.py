# Homework answer (Video 28): migrations 0003 + 0004
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

from app.database import engine
from tests.test_migrations import columns, version


def test_head_is_0004(client: TestClient) -> None:
    assert version() == "0004"
    assert columns("teachers") == ["id", "name"]


def test_is_published_defaults_to_false(client: TestClient) -> None:
    response = client.post("/courses", json={"title": "FastAPI Basics", "price": 299})
    assert response.json()["is_published"] is False
    response = client.post("/courses", json={"title": "Docker Deep Dive", "price": 499, "is_published": True})
    assert response.json()["is_published"] is True


def test_old_rows_are_not_published(client: TestClient, alembic_cfg: Config) -> None:
    command.downgrade(alembic_cfg, "0002")                          # before is_published
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO courses (title, price) VALUES ('Python 101', 99)"))
    command.upgrade(alembic_cfg, "head")
    assert client.get("/courses").json()[0]["is_published"] is False


def test_downgrade_two_steps(client: TestClient, alembic_cfg: Config) -> None:
    command.downgrade(alembic_cfg, "-2")
    assert version() == "0002"
    assert "is_published" not in columns("courses")
    assert "teachers" not in inspect(engine).get_table_names()
