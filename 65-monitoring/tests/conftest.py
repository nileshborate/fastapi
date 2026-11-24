# The tests talk to a REAL PostgreSQL (docker compose up -d db) - always the TEST database.
# The schema comes from the migrations, exactly like in production: alembic upgrade head.
import os
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://coursehub:coursehub-dev@127.0.0.1:5432/coursehub_test")
URL = os.environ["DATABASE_URL"]
ROOT = Path(__file__).resolve().parents[1]


def alembic_config() -> Config:
    cfg = Config(ROOT / "alembic.ini")
    cfg.attributes["configure_logger"] = False          # keep pytest's logging
    return cfg


def drop_everything() -> None:
    with psycopg.connect(URL, autocommit=True) as conn:
        conn.execute("DROP TABLE IF EXISTS courses, alembic_version")


@pytest.fixture(scope="session")
def cfg() -> Config:
    return alembic_config()


@pytest.fixture(autouse=True)
def at_head(cfg: Config) -> Iterator[None]:
    """every test starts - and ends - with the database at head"""
    command.upgrade(cfg, "head")
    yield
    command.upgrade(cfg, "head")


@pytest.fixture
def client() -> Iterator[TestClient]:
    from app import main  # imported here: AFTER DATABASE_URL is set

    with TestClient(main.app) as test_client:
        with main.db.connection() as conn:
            conn.execute("TRUNCATE courses RESTART IDENTITY")     # a clean table, ids from 1
        yield test_client


def pytest_sessionstart(session: pytest.Session) -> None:
    drop_everything()                                   # a fresh start: migrate from nothing
