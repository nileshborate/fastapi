# Homework answer (Video 27) - shown at the start of Video 28
from fastapi.testclient import TestClient

from tests.conftest import add_student, enroll


def test_full_course_is_409(client: TestClient) -> None:
    course = client.post("/courses", json={"title": "Small Batch", "price": 99, "max_students": 2}).json()
    for name in ["Asha", "Ravi"]:
        assert enroll(client, add_student(client, name)["id"], course["id"]).status_code == 201
    response = enroll(client, add_student(client, "Meera")["id"], course["id"])
    assert response.status_code == 409
    assert response.json() == {"detail": "Course is full"}


def test_max_students_default_is_30(client: TestClient) -> None:
    body = client.post("/courses", json={"title": "FastAPI Basics", "price": 299}).json()
    assert body["max_students"] == 30


def test_student_courses_list(client: TestClient) -> None:
    asha = add_student(client)
    for title in ["FastAPI Basics", "Python 101"]:
        course = client.post("/courses", json={"title": title, "price": 99}).json()
        enroll(client, asha["id"], course["id"])
    body = client.get(f"/students/{asha['id']}/courses").json()
    assert [c["title"] for c in body] == ["FastAPI Basics", "Python 101"]


def test_student_count(client: TestClient) -> None:
    course = client.post("/courses", json={"title": "FastAPI Basics", "price": 299}).json()
    assert course["student_count"] == 0
    for name in ["Asha", "Ravi"]:
        enroll(client, add_student(client, name)["id"], course["id"])
    assert client.get("/courses").json()[0]["student_count"] == 2
