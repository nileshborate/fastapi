from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.main import app
from app.models import Course
from app.schemas.course import CourseOut
from tests.conftest import ADMIN, TEACHER


def test_a_course_is_saved_in_the_database(client: TestClient) -> None:
    response = client.post("/courses", json={"title": "Docker Basics", "price": 99}, headers=TEACHER)
    assert response.json() == {"id": 1, "title": "Docker Basics", "price": 99.0}
    with SessionLocal() as db:                               # look inside the database directly
        course = db.scalars(select(Course).where(Course.title == "Docker Basics")).one()
        assert course.price == 99


def test_data_survives_a_restart(client: TestClient) -> None:
    client.post("/courses", json={"title": "Docker Basics", "price": 99}, headers=TEACHER)
    with TestClient(app) as new_client:                      # a new start of the app
        assert [c["title"] for c in new_client.get("/courses").json()] == ["Docker Basics"]


def test_filters_and_pagination_run_in_sql(client: TestClient) -> None:
    for i, price in enumerate([100, 200, 300, 400]):
        client.post("/courses", json={"title": f"Course {i}", "price": price}, headers=TEACHER)
    cheap = client.get("/courses", params={"max_price": 250}).json()
    assert [c["price"] for c in cheap] == [100, 200]
    page2 = client.get("/courses", params={"skip": 2, "limit": 1}).json()
    assert page2[0]["title"] == "Course 2"


def test_admin_stats_counts_in_the_database(client: TestClient) -> None:
    client.post("/courses", json={"title": "Docker Basics", "price": 99}, headers=TEACHER)
    assert client.get("/admin/stats", headers=ADMIN).json()["courses"] == 1


def test_get_db_gives_one_session_and_closes_it() -> None:
    dependency = get_db()
    db = next(dependency)                                    # setup: a new session
    assert isinstance(db, Session)
    dependency.close()                                       # runs the finally: db.close()


def test_schema_reads_a_model_object() -> None:
    course = Course(id=7, title="Docker Basics", price=99)
    out = CourseOut.model_validate(course)                   # works because of from_attributes=True
    assert out.model_dump() == {"id": 7, "title": "Docker Basics", "price": 99}
