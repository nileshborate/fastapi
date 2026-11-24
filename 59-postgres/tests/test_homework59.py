# Homework 59: a description column on an OLD table + the CI workflow with a PostgreSQL service
import os
from pathlib import Path

import psycopg
import yaml
from fastapi.testclient import TestClient

from app.db import Database

HERE = Path(__file__).resolve().parents[1]
CI = HERE.parent / ".github" / "workflows" / "ci-59.yml"
OLD = """CREATE TABLE courses (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title text NOT NULL CHECK (length(title) BETWEEN 3 AND 80),
    created_at timestamptz NOT NULL DEFAULT now())"""


def columns(conn: psycopg.Connection) -> list[str]:
    rows = conn.execute("SELECT column_name FROM information_schema.columns "
                        "WHERE table_name = 'courses' ORDER BY ordinal_position").fetchall()
    return [r[0] for r in rows]


def test_an_old_table_gets_the_column_and_keeps_its_rows() -> None:
    url = os.environ["DATABASE_URL"]
    with psycopg.connect(url, autocommit=True) as conn:          # the table from Video 59
        conn.execute("DROP TABLE IF EXISTS courses")
        conn.execute(OLD)
        conn.execute("INSERT INTO courses (title) VALUES ('Docker 101')")
        assert columns(conn) == ["id", "title", "created_at"]
    db = Database(url)
    db.open(wait_s=5)                                            # runs the SCHEMA again
    try:
        assert db.list_courses() == [{"id": 1, "title": "Docker 101", "description": None}]
    finally:
        db.close()
    with psycopg.connect(url) as conn:
        assert columns(conn) == ["id", "title", "created_at", "description"]


def test_a_course_with_a_description(client: TestClient) -> None:
    body = {"title": "Alembic", "description": "Migrations in production"}
    assert client.post("/courses", json=body).json() == {"id": 1, **body}
    too_long = {"title": "Long", "description": "x" * 501}
    assert client.post("/courses", json=too_long).status_code == 422


def test_ci_runs_pytest_against_a_postgres_service() -> None:
    job = yaml.safe_load(CI.read_text())["jobs"]["test"]
    pg = job["services"]["postgres"]
    assert pg["image"] == "postgres:16"
    assert "pg_isready -h 127.0.0.1" in pg["options"]            # the lesson of Video 59
    url = next(s["env"]["TEST_DATABASE_URL"] for s in job["steps"] if "env" in s)
    assert url.endswith(f"@localhost:5432/{pg['env']['POSTGRES_DB']}")
    assert f"{pg['env']['POSTGRES_USER']}:{pg['env']['POSTGRES_PASSWORD']}@" in url
