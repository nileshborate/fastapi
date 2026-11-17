# SQLite in a file - inside a container the file must live on a VOLUME, or it dies with it
import sqlite3

from app.config import get_settings


def connect() -> sqlite3.Connection:
    return sqlite3.connect(get_settings().db_path, timeout=1)


def init_db() -> None:
    with connect() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT)")


def add_course(title: str) -> int:
    with connect() as conn:
        return conn.execute("INSERT INTO courses (title) VALUES (?)", (title,)).lastrowid or 0


def list_courses() -> list[dict[str, object]]:
    with connect() as conn:
        rows = conn.execute("SELECT id, title FROM courses ORDER BY id").fetchall()
    return [{"id": i, "title": t} for i, t in rows]
