# Homework 60: rename title -> name with zero downtime (expand 0004, contract 0005),
# a safe NOT NULL, a readiness check that accepts a NEWER database, Compose in CI
from pathlib import Path

import psycopg
import pytest
import yaml
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from tests.conftest import URL

CI = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci-60.yml"


def sql(query: str, *params: object) -> list[tuple]:
    with psycopg.connect(URL) as conn:
        cur = conn.execute(query, params)
        return cur.fetchall() if cur.description else []


def columns() -> list[str]:
    return [r[0] for r in sql("SELECT column_name FROM information_schema.columns "
                              "WHERE table_name = 'courses' ORDER BY ordinal_position")]


def test_expand_backfills_name_for_the_old_rows(cfg: Config) -> None:
    command.downgrade(cfg, "0003")
    sql("INSERT INTO courses (title) SELECT 'Course ' || g FROM generate_series(1, 25) g")
    command.upgrade(cfg, "0004")
    assert sql("SELECT count(*) FROM courses WHERE name IS NULL OR name <> title") == [(0,)]


def test_at_0004_old_and_new_code_both_work(cfg: Config) -> None:
    command.downgrade(cfg, "0004")
    sql("TRUNCATE courses RESTART IDENTITY")
    sql("INSERT INTO courses (title) VALUES ('Old code')")        # 1.8.0 writes title
    sql("INSERT INTO courses (name) VALUES ('New code')")         # 1.9.x writes name
    sql("UPDATE courses SET name = 'Renamed' WHERE id = 1")
    assert sql("SELECT id, title, name FROM courses ORDER BY id") == [
        (1, "Renamed", "Renamed"), (2, "New code", "New code")]


def test_contract_removes_title_and_makes_name_not_null() -> None:   # at head: 0005
    assert "title" not in columns() and "name" in columns()
    assert sql("SELECT is_nullable FROM information_schema.columns "
               "WHERE table_name = 'courses' AND column_name = 'name'") == [("NO",)]
    assert sql("SELECT conname, convalidated FROM pg_constraint "
               "WHERE conrelid = 'courses'::regclass AND contype = 'c' ORDER BY conname") == [
        ("courses_level_check", True), ("courses_name_check", True)]


def test_why_contract_waits_for_the_old_code() -> None:
    with pytest.raises(psycopg.errors.UndefinedColumn):          # what 1.8.0 does at 0005
        sql("INSERT INTO courses (title) VALUES ('Old code')")


def test_validate_fails_while_rows_are_null(client: TestClient) -> None:
    client.post("/courses", json={"title": "No description"})
    sql("ALTER TABLE courses ADD CONSTRAINT d CHECK (description IS NOT NULL) NOT VALID")
    with pytest.raises(psycopg.errors.CheckViolation):           # backfill FIRST
        sql("ALTER TABLE courses VALIDATE CONSTRAINT d")
    sql("ALTER TABLE courses DROP CONSTRAINT d")


def test_a_newer_database_is_ready(client: TestClient) -> None:
    sql("UPDATE alembic_version SET version_num = '0006'")   # a revision this code can't know
    try:
        assert client.get("/health/ready").json()["revision"] == "0006"
    finally:
        sql("UPDATE alembic_version SET version_num = '0005'")


def test_ci_starts_the_whole_stack() -> None:
    steps = yaml.safe_load(CI.read_text())["jobs"]["compose"]["steps"]
    runs = "\n".join(s.get("run", "") for s in steps)
    assert "docker compose up -d --build --wait" in runs
    assert '"revision":"0005"' in runs
