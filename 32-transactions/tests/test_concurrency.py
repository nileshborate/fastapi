# Two requests, one row: played step by step with two sessions - and with real threads
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm.exc import StaleDataError

from app.database import SessionLocal, engine
from app.errors import ConflictError
from app.models import Course
from app.services import school_service
from tests.conftest import add_course, add_student


def test_read_modify_write_loses_an_update(client: TestClient) -> None:
    add_course(client, seats=1)
    with SessionLocal() as a, SessionLocal() as b:
        seats_a = a.get(Course, 1).seats_left               # A reads 1
        seats_b = b.get(Course, 1).seats_left               # B reads 1
        a.execute(update(Course).where(Course.id == 1).values(seats_left=seats_a - 1))
        a.commit()
        b.execute(update(Course).where(Course.id == 1).values(seats_left=seats_b - 1))
        b.commit()
    # two "successful" bookings for ONE seat - and seats_left says 0: the bug is invisible
    assert client.get("/courses/1").json()["seats_left"] == 0


def test_atomic_update_gives_the_seat_once(client: TestClient) -> None:
    add_course(client, seats=1)
    take = update(Course).where(Course.id == 1, Course.seats_left > 0).values(
        seats_left=Course.seats_left - 1
    )
    with SessionLocal() as a, SessionLocal() as b:
        first = a.execute(take)
        a.commit()
        second = b.execute(take)
        b.commit()
    assert (first.rowcount, second.rowcount) == (1, 0)      # B: "Course is full"


def test_version_id_col_stops_the_second_writer(client: TestClient) -> None:
    add_course(client)
    with SessionLocal() as a, SessionLocal() as b:
        course_a, course_b = a.get(Course, 1), b.get(Course, 1)
        course_a.fee = 349
        a.commit()                                          # version 1 -> 2
        course_b.fee = 399
        with pytest.raises(StaleDataError):
            b.commit()                                      # WHERE version = 1 -> 0 rows


def test_patch_with_an_old_version_is_409(client: TestClient) -> None:
    add_course(client)
    first = client.patch("/courses/1", json={"fee": 349, "version": 1})
    assert first.json()["version"] == 2
    second = client.patch("/courses/1", json={"fee": 399, "version": 1})
    assert second.status_code == 409
    assert client.get("/courses/1").json()["fee"] == 349    # the first change is kept


@pytest.mark.skipif(engine.dialect.name == "sqlite", reason="real parallel writers: PostgreSQL")
def test_twenty_threads_three_seats(client: TestClient) -> None:
    for k in range(20):
        add_student(client, f"Student {k}")
    add_course(client, seats=3)

    def try_enroll(student_id: int) -> bool:
        with SessionLocal() as db:
            try:
                school_service.enroll(db, student_id, 1)
                return True
            except ConflictError:
                return False

    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(try_enroll, range(1, 21)))
    assert results.count(True) == 3                         # exactly 3 - never 4
    assert client.get("/courses/1").json()["seats_left"] == 0
