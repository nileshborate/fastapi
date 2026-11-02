from fastapi.testclient import TestClient

from tests.conftest import add_course, add_teacher


def test_course_has_the_nested_teacher(client: TestClient) -> None:
    nilesh = add_teacher(client)
    response = client.post("/courses", json={"title": "FastAPI Basics", "price": 299, "teacher_id": nilesh["id"]})
    assert response.status_code == 201
    assert response.json() == {"id": 1, "title": "FastAPI Basics", "price": 299.0, "teacher": {"id": 1, "name": "Nilesh"}}


def test_unknown_teacher_is_404(client: TestClient) -> None:
    response = client.post("/courses", json={"title": "FastAPI Basics", "price": 299, "teacher_id": 42})
    assert response.status_code == 404
    assert response.json() == {"detail": "Teacher not found"}


def test_teacher_id_is_required(client: TestClient) -> None:
    response = client.post("/courses", json={"title": "FastAPI Basics", "price": 299})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "teacher_id"]


def test_duplicate_title_is_409(client: TestClient) -> None:
    nilesh = add_teacher(client)
    add_course(client, "FastAPI Basics", nilesh["id"])
    response = client.post("/courses", json={"title": "FastAPI Basics", "price": 1, "teacher_id": nilesh["id"]})
    assert response.status_code == 409


def test_list_courses_with_teachers(client: TestClient) -> None:
    nilesh, priya = add_teacher(client), add_teacher(client, "Priya", "Python")
    add_course(client, "FastAPI Basics", nilesh["id"])
    add_course(client, "Python 101", priya["id"])
    body = client.get("/courses").json()
    assert [(c["title"], c["teacher"]["name"]) for c in body] == [("FastAPI Basics", "Nilesh"), ("Python 101", "Priya")]


def test_get_and_delete_course(client: TestClient) -> None:
    course = add_course(client, "FastAPI Basics", add_teacher(client)["id"])
    assert client.get(f"/courses/{course['id']}").json()["teacher"]["name"] == "Nilesh"
    assert client.delete(f"/courses/{course['id']}").status_code == 204
    assert client.get(f"/courses/{course['id']}").json() == {"detail": "Course not found"}
