# PostgreSQL through a connection pool - opened at startup, shared by every request
from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

SCHEMA = """
CREATE TABLE IF NOT EXISTS courses (
    id         integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title      text NOT NULL CHECK (length(title) BETWEEN 3 AND 80),
    created_at timestamptz NOT NULL DEFAULT now()
);
-- homework 59: IF NOT EXISTS above skips an EXISTING table - a new column needs its own ALTER
ALTER TABLE courses ADD COLUMN IF NOT EXISTS description text;
"""


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
        with self.connection() as conn:
            conn.execute(SCHEMA)

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

    def ping(self) -> bool:
        try:
            with self.connection(timeout=1) as conn:
                conn.execute("SELECT 1")
        except psycopg.Error:
            return False
        return True

    def add_course(self, title: str, description: str | None = None) -> dict:
        with self.connection() as conn:
            # %s = a parameter: sent apart from the SQL, never pasted into it
            return conn.execute(
                "INSERT INTO courses (title, description) VALUES (%s, %s)"
                " RETURNING id, title, description", (title, description)).fetchone()

    def list_courses(self) -> list[dict]:
        with self.connection() as conn:
            return conn.execute(
                "SELECT id, title, description FROM courses ORDER BY id").fetchall()
