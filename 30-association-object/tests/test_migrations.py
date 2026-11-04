# The migrations: 0001 = a plain link table, 0002 = the link gets its own data
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import Base, engine


def test_only_one_head(alembic_cfg: Config) -> None:
    assert ScriptDirectory.from_config(alembic_cfg).get_heads() == ["0003"]


def test_models_match_the_migrations(client: TestClient) -> None:
    with engine.connect() as conn:
        assert compare_metadata(MigrationContext.configure(conn), Base.metadata) == []


def test_old_links_survive_and_get_a_date(client: TestClient, alembic_cfg: Config) -> None:
    command.downgrade(alembic_cfg, "0001")                     # the plain link table: 2 columns
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO students (name, email) VALUES ('Asha', 'asha@example.com')"))
        conn.execute(text("INSERT INTO courses (title, fee) VALUES ('FastAPI Basics', 299)"))
        conn.execute(text("INSERT INTO enrollments (student_id, course_id) VALUES (1, 1)"))
    command.upgrade(alembic_cfg, "head")                       # + enrolled_at, grade
    row = client.get("/students/1").json()["enrollments"][0]
    assert row["course"]["title"] == "FastAPI Basics"
    assert row["enrolled_at"] is not None                     # the time of the migration
    assert row["grade"] is None
