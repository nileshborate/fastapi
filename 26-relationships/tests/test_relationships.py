# What happens INSIDE: foreign keys, the relationship objects, and the number of queries
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, inspect
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal, engine
from app.models import Course, Teacher
from tests.conftest import add_course, add_teacher


def test_the_foreign_key_is_in_the_table(client: TestClient) -> None:
    fks = inspect(engine).get_foreign_keys("courses")
    assert [(fk["constrained_columns"], fk["referred_table"], fk["referred_columns"]) for fk in fks] == [
        (["teacher_id"], "teachers", ["id"])]


def test_the_database_refuses_an_unknown_teacher(client: TestClient) -> None:
    with SessionLocal() as db:                         # WITHOUT our service check
        db.add(Course(title="Ghost course", price=1, teacher_id=42))
        with pytest.raises(IntegrityError, match="(?i)foreign key"):
            db.commit()                                # PRAGMA foreign_keys=ON does this


def test_back_populates_keeps_both_sides_in_sync(client: TestClient) -> None:
    teacher = Teacher(name="Nilesh", subject="FastAPI")
    course = Course(title="FastAPI Basics", price=299, teacher=teacher)     # set ONE side ...
    assert teacher.courses == [course]                                       # ... the other follows


def test_list_courses_needs_only_two_queries(client: TestClient) -> None:
    for i in range(5):
        add_course(client, f"Course {i}", add_teacher(client, f"Teacher {i}")["id"])
    selects: list[str] = []

    def count(conn: Any, cursor: Any, statement: str, *args: Any) -> None:
        if statement.startswith("SELECT"): selects.append(statement)

    event.listen(engine, "before_cursor_execute", count)
    try:
        assert len(client.get("/courses").json()) == 5
    finally:
        event.remove(engine, "before_cursor_execute", count)
    assert len(selects) == 2                           # courses + their teachers (selectinload)
