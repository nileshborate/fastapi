# Homework answer (Video 32): unenroll with a refund, an atomic top-up
from fastapi.testclient import TestClient
from sqlalchemy import update

from app.database import SessionLocal
from app.models import Student
from tests.conftest import add_course, add_student, enroll


def test_unenroll_gives_seat_and_money_back(client: TestClient) -> None:
    add_student(client)
    add_course(client, seats=1)
    enroll(client, 1)                                         # 500 -> 201, 1 seat -> 0
    assert client.delete("/enrollments/1/1").status_code == 204
    assert client.get("/students/1").json()["balance"] == 500
    assert client.get("/courses/1").json()["seats_left"] == 1


def test_unenroll_twice_is_404_and_changes_nothing(client: TestClient) -> None:
    add_student(client)
    add_course(client, seats=1)
    enroll(client, 1)
    client.delete("/enrollments/1/1")
    response = client.delete("/enrollments/1/1")
    assert response.json() == {"detail": "Enrollment not found"}
    assert client.get("/students/1").json()["balance"] == 500   # no second refund


def test_top_up(client: TestClient) -> None:
    add_student(client)
    assert client.post("/students/1/top-up", json={"amount": 200}).json()["balance"] == 700
    assert client.post("/students/1/top-up", json={"amount": 10_001}).status_code == 422
    assert client.post("/students/1/top-up", json={"amount": 0}).status_code == 422
    assert client.post("/students/9/top-up", json={"amount": 5}).status_code == 404


def test_two_sessions_top_up_both_arrive(client: TestClient) -> None:
    add_student(client)                                       # 500
    add_more = update(Student).where(Student.id == 1)
    with SessionLocal() as a, SessionLocal() as b:
        a.get(Student, 1), b.get(Student, 1)                  # both READ 500 ...
        a.execute(add_more.values(balance=Student.balance + 100))
        a.commit()
        b.execute(add_more.values(balance=Student.balance + 200))
        b.commit()
    assert client.get("/students/1").json()["balance"] == 800   # ... and nothing is lost
