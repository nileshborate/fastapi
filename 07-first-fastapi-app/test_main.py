# Run:  pip install pytest   then   pytest -v
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_home() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Course Hub API"}


def test_courses() -> None:
    response = client.get("/courses")
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_unknown_route_returns_404() -> None:
    assert client.get("/unknown").status_code == 404


def test_wrong_method_returns_405() -> None:
    assert client.post("/").status_code == 405
