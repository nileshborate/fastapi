# PostgreSQL through a connection pool. NO schema code here any more: Alembic owns the schema.
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import psycopg
from alembic.config import Config
from alembic.script import ScriptDirectory
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


def head_revision() -> str:
    """The newest migration in THIS code - what the database must be at"""
    return ScriptDirectory.from_config(Config(ALEMBIC_INI)).get_current_head() or ""


def known_revisions() -> set[str]:
    """Every migration THIS code knows - a revision that isn't here is newer than the code"""
    script = ScriptDirectory.from_config(Config(ALEMBIC_INI))
    return {s.revision for s in script.walk_revisions()}


class Database:
    def __init__(self, url: str) -> None:
        self.url = url
        self.pool: ConnectionPool | None = None

    def open(self, wait_s: float) -> None:
        self.pool = ConnectionPool(self.url, min_size=1, max_size=5, open=False,
                                   kwargs={"row_factory": dict_row})
        try:
            self.pool.open(wait=True, timeout=wait_s)    # PoolTimeout: no database in time
        except psycopg.OperationalError:
            self.close()
            raise

    def close(self) -> None:
        if self.pool is not None:
            self.pool.close()
            self.pool = None

    @contextmanager
    def connection(self, timeout: float = 5) -> Iterator[psycopg.Connection]:
        if self.pool is None:
            raise psycopg.OperationalError("the pool is not open")
        with self.pool.connection(timeout=timeout) as conn:   # commit at the end, or roll back
            yield conn

    def revision(self) -> str | None:
        """The migration the database is at - None = unreachable"""
        try:
            with self.connection(timeout=1) as conn:
                row = conn.execute("SELECT to_regclass('alembic_version') AS t").fetchone()
                if row is None or row["t"] is None:
                    return ""                                  # never migrated
                row = conn.execute("SELECT version_num FROM alembic_version").fetchone()
                return row["version_num"] if row else ""
        except psycopg.Error:
            return None

    # homework 60: the column is "name" now - the API still says "title" (its contract)
    def add_course(self, title: str, description: str | None, level: str) -> dict:
        with self.connection() as conn:
            return conn.execute(
                "INSERT INTO courses (name, description, level) VALUES (%s, %s, %s)"
                " RETURNING id, name AS title, description, level",
                (title, description, level)).fetchone()

    def get_course(self, course_id: int) -> dict | None:
        with self.connection() as conn:
            return conn.execute(
                "SELECT id, name AS title, description, level FROM courses WHERE id = %s",
                (course_id,)).fetchone()

    def list_courses(self) -> list[dict]:
        with self.connection() as conn:
            return conn.execute(
                "SELECT id, name AS title, description, level FROM courses ORDER BY id"
            ).fetchall()
