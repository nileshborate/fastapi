# Inside the database: the link table itself
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, insert, select
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal, engine
from app.models import Course, Student, enrollments
from tests.conftest import add_course, add_student, enroll


def test_the_link_table(client: TestClient) -> None:
    info = inspect(engine)
    assert info.get_pk_constraint("enrollments")["constrained_columns"] == ["student_id", "course_id"]
    assert sorted(fk["referred_table"] for fk in info.get_foreign_keys("enrollments")) == ["courses", "students"]


def test_one_row_per_enrollment(client: TestClient) -> None:
    asha, course = add_student(client), add_course(client)
    enroll(client, asha["id"], course["id"])
    with SessionLocal() as db:
        assert db.execute(select(enrollments)).all() == [(asha["id"], course["id"])]


def test_the_database_refuses_the_same_pair_twice(client: TestClient) -> None:
    asha, course = add_student(client), add_course(client)
    enroll(client, asha["id"], course["id"])
    with SessionLocal() as db, pytest.raises(IntegrityError):
        db.execute(insert(enrollments).values(student_id=asha["id"], course_id=course["id"]))
        db.commit()


def test_append_in_python(client: TestClient) -> None:
    with SessionLocal() as db:
        asha = Student(name="Asha", email="asha@example.com")
        course = Course(title="FastAPI Basics", price=299)
        asha.courses.append(course)                   # one side ...
        assert course.students == [asha]              # ... back_populates updates the other
        db.add(asha)                                  # the course is saved too (cascade "save-update")
        db.commit()
        assert db.scalar(select(Course.title)) == "FastAPI Basics"
