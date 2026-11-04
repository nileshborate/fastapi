# The migrations themselves: upgrade, downgrade, and data that survives
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

from app.database import Base, engine


def columns(table: str) -> list[str]:
    return [c["name"] for c in inspect(engine).get_columns(table)]


def version() -> str | None:
    with engine.connect() as conn:
        return MigrationContext.configure(conn).get_current_revision()


def test_head_creates_the_tables(client: TestClient) -> None:
    assert sorted(inspect(engine).get_table_names()) == ["alembic_version", "courses", "teachers"]
    assert columns("courses") == ["id", "title", "price", "level", "is_published"]
    assert version() == "0004"


def test_downgrade_one_step(client: TestClient, alembic_cfg: Config) -> None:
    command.downgrade(alembic_cfg, "-1")
    assert version() == "0003"
    assert "teachers" not in inspect(engine).get_table_names()     # 0004 is undone


def test_downgrade_to_base(client: TestClient, alembic_cfg: Config) -> None:
    command.downgrade(alembic_cfg, "base")
    assert inspect(engine).get_table_names() == ["alembic_version"]
    assert version() is None


def test_old_rows_survive_and_get_the_default(client: TestClient, alembic_cfg: Config) -> None:
    command.downgrade(alembic_cfg, "0001")                          # the database BEFORE "level"
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO courses (title, price) VALUES ('FastAPI Basics', 299), ('Python 101', 99)"))
    command.upgrade(alembic_cfg, "head")                            # add the column - keep the data
    assert client.get("/courses").json() == [
        {"id": 1, "title": "FastAPI Basics", "price": 299.0, "level": "beginner", "is_published": False},
        {"id": 2, "title": "Python 101", "price": 99.0, "level": "beginner", "is_published": False},
    ]


def test_models_match_the_migrations(client: TestClient) -> None:
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    assert diff == []                                               # models and database agree
