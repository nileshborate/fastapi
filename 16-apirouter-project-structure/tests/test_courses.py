# Run from the project folder:  pytest -v
from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    assert client.get("/").json() == {"status": "ok"}


def test_create_and_list_courses(client: TestClient) -> None:
    response = client.post("/courses", json={"title": "FastAPI Basics", "price": 499})
    assert response.status_code == 201
    assert response.json() == {"id": 1, "title": "FastAPI Basics", "price": 499.0}
    assert client.get("/courses").json() == [{"id": 1, "title": "FastAPI Basics", "price": 499.0}]


def test_get_course_404(client: TestClient) -> None:
    response = client.get("/courses/99")
    assert response.status_code == 404
    assert response.json() == {"detail": "Course not found"}


def test_delete_course(client: TestClient) -> None:
    client.post("/courses", json={"title": "FastAPI Basics", "price": 499})
    assert client.delete("/courses/1").status_code == 204
    assert client.delete("/courses/1").status_code == 404


def test_tags_in_openapi(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert paths["/courses"]["get"]["tags"] == ["Courses"]
    assert paths["/students"]["get"]["tags"] == ["Students"]
