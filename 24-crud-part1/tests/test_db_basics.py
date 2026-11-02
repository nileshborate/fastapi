import sqlite3

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db_basics import sql_basics
from db_basics.orm_basics import Course, Student, find_student_by_email, make_engine


@pytest.fixture
def conn() -> sqlite3.Connection:
    return sql_basics.connect(":memory:")          # a database that lives only in memory


def test_join_finds_the_courses_of_a_student(conn: sqlite3.Connection) -> None:
    fastapi = sql_basics.add_course(conn, "FastAPI Basics", 299)
    sql_basics.add_course(conn, "Async Python", 249)
    asha = sql_basics.add_student(conn, "Asha", "asha@example.com")
    sql_basics.enroll(conn, asha, fastapi)
    assert sql_basics.courses_of(conn, "Asha") == ["FastAPI Basics"]


def test_foreign_key_blocks_a_missing_course(conn: sqlite3.Connection) -> None:
    asha = sql_basics.add_student(conn, "Asha", "asha@example.com")
    with pytest.raises(sqlite3.IntegrityError):
        sql_basics.enroll(conn, asha, 99)


def test_unique_title(conn: sqlite3.Connection) -> None:
    sql_basics.add_course(conn, "FastAPI Basics", 299)
    with pytest.raises(sqlite3.IntegrityError):
        sql_basics.add_course(conn, "FastAPI Basics", 100)


def test_sql_injection(conn: sqlite3.Connection) -> None:
    sql_basics.add_student(conn, "Asha", "asha@example.com")
    sql_basics.add_student(conn, "Ravi", "ravi@example.com")
    attack = "x' OR '1'='1"
    assert len(sql_basics.find_student_unsafe(conn, attack)) == 2    # leaks every student
    assert sql_basics.find_student_safe(conn, attack) == []          # a parameter is just a value


def test_orm_create_query_update() -> None:
    engine = make_engine("sqlite://")                                 # in memory
    with Session(engine) as session:
        session.add_all([
            Course(title="FastAPI Basics", price=299),
            Course(title="Pydantic Models", price=199),
        ])
        session.commit()
        cheap = session.scalars(select(Course).where(Course.price < 250)).all()
        assert [c.title for c in cheap] == ["Pydantic Models"]
        course = session.get(Course, 1)
        assert course is not None
        course.price = 349
        session.commit()
        assert session.get(Course, 1).price == 349                   # type: ignore[union-attr]


def test_orm_unique_title() -> None:
    engine = make_engine("sqlite://")
    with Session(engine) as session:
        session.add_all([Course(title="Same", price=1), Course(title="Same", price=2)])
        with pytest.raises(IntegrityError):
            session.commit()


# ---------------------------------------------------------------- homework answer (Video 22)
def test_courses_of_a_teacher(conn: sqlite3.Connection) -> None:
    meera = sql_basics.add_teacher(conn, "Meera")
    sql_basics.add_course(conn, "FastAPI Basics", 299, teacher_id=meera)
    sql_basics.add_course(conn, "Async Python", 249, teacher_id=meera)
    sql_basics.add_course(conn, "Pydantic Models", 199)                # no teacher yet
    assert sql_basics.courses_of_teacher(conn, "Meera") == ["Async Python", "FastAPI Basics"]


def test_teacher_must_exist(conn: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        sql_basics.add_course(conn, "FastAPI Basics", 299, teacher_id=99)


def test_delete_with_sql(conn: sqlite3.Connection) -> None:
    course_id = sql_basics.add_course(conn, "FastAPI Basics", 299)
    sql_basics.delete_course(conn, course_id)
    assert conn.execute("SELECT COUNT(*) FROM courses").fetchone() == (0,)


def test_orm_student_by_email_and_delete() -> None:
    engine = make_engine("sqlite://")
    with Session(engine) as session:
        session.add_all([
            Student(name="Asha", email="asha@example.com"),
            Student(name="Ravi", email="ravi@example.com"),
            Course(title="FastAPI Basics", price=299),
        ])
        session.commit()
        ravi = find_student_by_email(session, "ravi@example.com")
        assert ravi is not None and ravi.name == "Ravi"
        assert find_student_by_email(session, "nobody@example.com") is None
        course = session.get(Course, 1)
        session.delete(course)                                          # DELETE with the ORM
        session.commit()
        assert session.get(Course, 1) is None
