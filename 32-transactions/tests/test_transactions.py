# All or nothing: the seat, the payment and the enrollment - in ONE transaction
from fastapi.testclient import TestClient

from tests.conftest import add_course, add_student, enroll


def state(client: TestClient, student_id: int = 1) -> tuple[int, int]:
    balance = client.get(f"/students/{student_id}").json()["balance"]
    seats = client.get("/courses/1").json()["seats_left"]
    return balance, seats


def test_enroll_takes_a_seat_and_pays(client: TestClient) -> None:
    add_student(client)
    add_course(client)
    response = enroll(client, 1)
    assert response.status_code == 201
    assert response.json() == {"student_id": 1, "course_id": 1, "balance": 201, "seats_left": 1}


def test_not_enough_balance_rolls_back_the_seat(client: TestClient) -> None:
    add_student(client, "Ravi", balance=100)
    add_course(client, seats=1)
    assert enroll(client, 1).json() == {"detail": "Not enough balance"}
    assert state(client) == (100, 1)              # the seat from step 1 is back


def test_full_course_changes_nothing(client: TestClient) -> None:
    add_student(client, "Asha")
    add_student(client, "Ravi")
    add_course(client, seats=1)
    enroll(client, 1)
    assert enroll(client, 2).json() == {"detail": "Course is full"}
    assert state(client, 2) == (500, 0)           # Ravi paid nothing


def test_already_enrolled_rolls_back_seat_and_payment(client: TestClient) -> None:
    add_student(client, balance=1000)
    add_course(client, seats=5)
    enroll(client, 1)
    assert enroll(client, 1).json() == {"detail": "Already enrolled"}
    assert state(client) == (701, 4)              # paid ONCE, ONE seat


def test_unknown_student_or_course(client: TestClient) -> None:
    add_course(client)
    assert enroll(client, 9).json() == {"detail": "Student not found"}
    add_student(client)
    assert enroll(client, 1, 9).json() == {"detail": "Course not found"}
