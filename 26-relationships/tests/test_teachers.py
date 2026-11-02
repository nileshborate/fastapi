from fastapi.testclient import TestClient

from tests.conftest import add_course, add_teacher


def test_create_and_list_teachers(client: TestClient) -> None:
    add_teacher(client, "Nilesh")
    add_teacher(client, "Priya", "Python")
    assert [t["name"] for t in client.get("/teachers").json()] == ["Nilesh", "Priya"]


def test_teacher_detail_has_the_courses(client: TestClient) -> None:
    nilesh = add_teacher(client)
    add_course(client, "FastAPI Basics", nilesh["id"], 299)
    add_course(client, "Async Python", nilesh["id"], 249)
    body = client.get(f"/teachers/{nilesh['id']}").json()
    assert body == {"id": 1, "name": "Nilesh", "subject": "FastAPI", "course_count": 2, "courses": [
        {"id": 1, "title": "FastAPI Basics", "price": 299.0},
        {"id": 2, "title": "Async Python", "price": 249.0},
    ]}


def test_teacher_courses_endpoint(client: TestClient) -> None:
    nilesh, priya = add_teacher(client), add_teacher(client, "Priya", "Python")
    add_course(client, "FastAPI Basics", nilesh["id"])
    add_course(client, "Python 101", priya["id"])
    body = client.get(f"/teachers/{priya['id']}/courses").json()
    assert [(c["title"], c["teacher"]["name"]) for c in body] == [("Python 101", "Priya")]


def test_teacher_404(client: TestClient) -> None:
    assert client.get("/teachers/9").json() == {"detail": "Teacher not found"}
    assert client.get("/teachers/9/courses").status_code == 404


def test_delete_teacher_with_courses_is_409(client: TestClient) -> None:
    nilesh = add_teacher(client)
    add_course(client, "FastAPI Basics", nilesh["id"])
    add_course(client, "Async Python", nilesh["id"])
    response = client.delete(f"/teachers/{nilesh['id']}")
    assert response.status_code == 409
    assert response.json() == {"detail": "Teacher still has 2 courses"}


def test_delete_teacher_without_courses(client: TestClient) -> None:
    nilesh = add_teacher(client)
    course = add_course(client, "FastAPI Basics", nilesh["id"])
    client.delete(f"/courses/{course['id']}")                        # first the course ...
    assert client.delete(f"/teachers/{nilesh['id']}").status_code == 204   # ... then the teacher
    assert client.get(f"/teachers/{nilesh['id']}").status_code == 404
