# The migrations themselves: one head, models == database, renames and data migrations keep the data
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

from app.database import Base, engine


def columns(table: str) -> list[str]:
    return [c["name"] for c in inspect(engine).get_columns(table)]


def version() -> str | None:
    with engine.connect() as conn:
        return MigrationContext.configure(conn).get_current_revision()


def test_only_one_head(alembic_cfg: Config) -> None:
    heads = ScriptDirectory.from_config(alembic_cfg).get_heads()
    assert heads == ["0008"]                                       # two heads? -> alembic merge heads


def test_models_match_the_migrations(client: TestClient) -> None:
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    assert diff == []                                              # the same check as "alembic check"


def test_head_columns(client: TestClient) -> None:
    assert version() == "0008"
    assert sorted(columns("courses")) == ["description", "fee", "fee_paise", "id", "level", "slug", "teacher_id", "title"]
    # sorted: the two branches (0005, 0006) have no fixed order - and they don't need one


def test_rename_keeps_the_data(client: TestClient, alembic_cfg: Config) -> None:
    command.downgrade(alembic_cfg, "0002")                         # still "price"
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO courses (title, price) VALUES ('FastAPI Basics', 299)"))
    command.upgrade(alembic_cfg, "head")
    assert client.get("/courses").json()[0]["fee"] == 299.0        # price -> fee, the value is still there


def test_data_migration_fills_old_rows(client: TestClient, alembic_cfg: Config) -> None:
    command.downgrade(alembic_cfg, "0003")                         # before "slug"
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO courses (title, fee) VALUES ('FastAPI Basics', 299), ('Python 101!', 99)"))
    command.upgrade(alembic_cfg, "head")
    courses = client.get("/courses").json()
    assert [c["slug"] for c in courses] == ["fastapi-basics", "python-101"]
    assert [c["level"] for c in courses] == ["beginner", "beginner"]


def test_full_round_trip(client: TestClient, alembic_cfg: Config) -> None:
    command.downgrade(alembic_cfg, "base")                         # every downgrade() works ...
    assert inspect(engine).get_table_names() == ["alembic_version"]
    command.upgrade(alembic_cfg, "head")                           # ... and every upgrade() again
    assert version() == "0008"
