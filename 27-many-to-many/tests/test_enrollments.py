from fastapi.testclient import TestClient

from tests.conftest import add_course, add_student, enroll


def test_enroll(client: TestClient) -> None:
    asha, course = add_student(client), add_course(client)
    response = enroll(client, asha["id"], course["id"])
    assert response.status_code == 201
    assert response.json()["courses"] == [{"id": 1, "title": "FastAPI Basics", "price": 299.0, "max_students": 30, "student_count": 1}]


def test_both_sides_see_the_enrollment(client: TestClient) -> None:
    asha, ravi = add_student(client), add_student(client, "Ravi")
    fastapi, python = add_course(client), add_course(client, "Python 101", 99)
    enroll(client, asha["id"], fastapi["id"])
    enroll(client, asha["id"], python["id"])
    enroll(client, ravi["id"], fastapi["id"])
    assert [c["title"] for c in client.get(f"/students/{asha['id']}").json()["courses"]] == ["FastAPI Basics", "Python 101"]
    assert [s["name"] for s in client.get(f"/courses/{fastapi['id']}").json()["students"]] == ["Asha", "Ravi"]


def test_enroll_twice_is_409(client: TestClient) -> None:
    asha, course = add_student(client), add_course(client)
    enroll(client, asha["id"], course["id"])
    response = enroll(client, asha["id"], course["id"])
    assert response.status_code == 409
    assert response.json() == {"detail": "Already enrolled"}


def test_enroll_unknown_student_or_course_is_404(client: TestClient) -> None:
    asha, course = add_student(client), add_course(client)
    assert enroll(client, 42, course["id"]).json() == {"detail": "Student not found"}
    assert enroll(client, asha["id"], 42).json() == {"detail": "Course not found"}


def test_unenroll(client: TestClient) -> None:
    asha, course = add_student(client), add_course(client)
    enroll(client, asha["id"], course["id"])
    url = f"/students/{asha['id']}/courses/{course['id']}"
    assert client.delete(url).status_code == 204
    assert client.get(f"/students/{asha['id']}").json()["courses"] == []
    assert client.delete(url).json() == {"detail": "Enrollment not found"}      # not enrolled any more


def test_delete_student_keeps_the_course(client: TestClient) -> None:
    asha, course = add_student(client), add_course(client)
    enroll(client, asha["id"], course["id"])
    assert client.delete(f"/students/{asha['id']}").status_code == 204
    assert client.get(f"/courses/{course['id']}").json()["students"] == []     # the link is gone, the course stays


def test_delete_course_keeps_the_student(client: TestClient) -> None:
    asha, course = add_student(client), add_course(client)
    enroll(client, asha["id"], course["id"])
    assert client.delete(f"/courses/{course['id']}").status_code == 204
    assert client.get(f"/students/{asha['id']}").json()["courses"] == []
