# A tiny SQLite database - our CRITICAL dependency
import sqlite3

from app.config import get_settings

COURSES = [(1, "Python Basics"), (2, "SQL Joins"), (3, "FastAPI Mastery")]


def connect() -> sqlite3.Connection:
    return sqlite3.connect(get_settings().db_path, timeout=1)


def init_db() -> None:
    with connect() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT)")
        conn.executemany("INSERT OR IGNORE INTO courses VALUES (?, ?)", COURSES)


def list_courses() -> list[dict[str, object]]:
    with connect() as conn:
        rows = conn.execute("SELECT id, title FROM courses ORDER BY id").fetchall()
    return [{"id": i, "title": t} for i, t in rows]
