# Run:  pytest -v
import copy
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)
ORIGINAL = copy.deepcopy(main.COURSES)


@pytest.fixture(autouse=True)
def reset_data() -> Iterator[None]:
    main.COURSES[:] = copy.deepcopy(ORIGINAL)
    yield


def test_create_course() -> None:
    response = client.post("/courses", json={"title": "Testing FastAPI", "price": 299})
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 4
    assert body["level"] == "beginner"   # default value
    assert len(client.get("/courses").json()) == 4


def test_title_is_required() -> None:
    response = client.post("/courses", json={"price": 299})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "title"]


def test_wrong_type() -> None:
    assert client.post("/courses", json={"title": "X", "price": "abc"}).status_code == 422


def test_numeric_string_is_converted() -> None:
    assert client.post("/courses", json={"title": "X", "price": "499"}).json()["price"] == 499


def test_extra_fields_are_ignored() -> None:
    assert "teacher" not in client.post("/courses", json={"title": "X", "teacher": "Nilesh"}).json()


def test_replace_course() -> None:
    response = client.put("/courses/2", json={"title": "Pydantic V2", "price": 599})
    assert response.status_code == 200
    assert response.json() == {"id": 2, "title": "Pydantic V2", "level": "beginner", "price": 599, "published": False, "description": None}


def test_replace_missing_course() -> None:
    assert client.put("/courses/99", json={"title": "X"}).status_code == 404


def test_body_path_and_query() -> None:
    response = client.post("/courses/1/reviews?notify=true", json={"student": "Asha", "rating": 5})
    assert response.status_code == 201
    assert response.json() == {"course_id": 1, "review": {"student": "Asha", "rating": 5, "comment": None}, "notify": True}
