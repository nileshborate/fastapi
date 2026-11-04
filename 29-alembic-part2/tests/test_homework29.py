# Homework answer (Video 29): rename teachers -> instructors (keep the rows) + fee_paise (a data migration)
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

from app.database import engine


def test_teachers_table_is_now_instructors(client: TestClient) -> None:
    tables = inspect(engine).get_table_names()
    assert "instructors" in tables and "teachers" not in tables
    fk = inspect(engine).get_foreign_keys("courses")[0]
    assert fk["referred_table"] == "instructors"


def test_old_rows_keep_their_teacher(client: TestClient, alembic_cfg: Config) -> None:
    command.downgrade(alembic_cfg, "0007")                          # still "teachers", no fee_paise
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO teachers (name) VALUES ('Nilesh')"))
        conn.execute(text("INSERT INTO courses (title, fee, slug, teacher_id) VALUES ('FastAPI Basics', 299.5, 'fastapi-basics', 1)"))
    command.upgrade(alembic_cfg, "head")
    course = client.get("/courses").json()[0]
    assert course["teacher_id"] == 1                                # the link survived the rename
    assert course["fee_paise"] == 29950                             # 299.5 * 100 - filled by the migration
    assert client.get("/teachers").json() == [{"id": 1, "name": "Nilesh"}]


def test_new_course_gets_fee_paise(client: TestClient) -> None:
    response = client.post("/courses", json={"title": "Docker", "fee": 499.99})
    assert response.json()["fee_paise"] == 49999


def test_downgrade_brings_teachers_back(client: TestClient, alembic_cfg: Config) -> None:
    command.downgrade(alembic_cfg, "-1")
    assert "teachers" in inspect(engine).get_table_names()
    assert "fee_paise" not in [c["name"] for c in inspect(engine).get_columns("courses")]
