from fastapi.testclient import TestClient


def test_create_course_makes_a_slug(client: TestClient) -> None:
    response = client.post("/courses", json={"title": "FastAPI Basics!", "fee": 299})
    assert response.status_code == 201
    assert response.json() == {
        "id": 1, "title": "FastAPI Basics!", "fee": 299.0, "slug": "fastapi-basics",
        "level": "beginner", "description": None, "teacher_id": None,
    }


def test_course_with_a_teacher(client: TestClient) -> None:
    teacher = client.post("/teachers", json={"name": "Nilesh"}).json()
    response = client.post("/courses", json={"title": "Docker", "fee": 499, "teacher_id": teacher["id"]})
    assert response.json()["teacher_id"] == teacher["id"]


def test_unknown_teacher_is_404(client: TestClient) -> None:
    response = client.post("/courses", json={"title": "Docker", "fee": 499, "teacher_id": 99})
    assert response.status_code == 404


def test_duplicate_title_is_409(client: TestClient) -> None:
    client.post("/courses", json={"title": "FastAPI Basics", "fee": 299})
    assert client.post("/courses", json={"title": "FastAPI Basics", "fee": 1}).status_code == 409
