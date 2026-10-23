# Run:  pytest -v
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)
VALID: dict[str, Any] = {"name": "Asha Patil", "email": "asha@example.com"}


@pytest.fixture(autouse=True)
def reset_data() -> Iterator[None]:
    main.STUDENTS.clear()
    yield


def error_type(body: dict[str, Any]) -> str:
    response = client.post("/students", json=body)
    assert response.status_code == 422
    return str(response.json()["detail"][0]["type"])


def test_create_student_with_defaults() -> None:
    response = client.post("/students", json=VALID)
    assert response.status_code == 201
    assert response.json() == {"id": 1, "name": "Asha Patil", "email": "asha@example.com", "age": None, "phone": None, "courses": []}


def test_name_too_short() -> None:
    assert error_type({**VALID, "name": "A"}) == "string_too_short"


def test_invalid_email() -> None:
    assert error_type({**VALID, "email": "not-an-email"}) == "value_error"


def test_age_limits() -> None:
    assert error_type({**VALID, "age": 5}) == "greater_than_equal"
    assert error_type({**VALID, "age": 101}) == "less_than_equal"


def test_age_is_strict() -> None:
    assert error_type({**VALID, "age": "20"}) == "int_type"


def test_phone_pattern() -> None:
    assert error_type({**VALID, "phone": "12345"}) == "string_pattern_mismatch"
    assert client.post("/students", json={**VALID, "phone": "9876543210"}).status_code == 201


def test_courses_max_length() -> None:
    assert error_type({**VALID, "courses": [1, 2, 3, 4, 5, 6]}) == "too_long"


def test_default_list_is_not_shared() -> None:
    first = client.post("/students", json=VALID).json()
    second = client.post("/students", json=VALID).json()
    assert first["courses"] == [] and second["courses"] == []


def test_replace_missing_student() -> None:
    assert client.put("/students/99", json=VALID).status_code == 404


def test_annotated_course_title() -> None:
    assert client.post("/courses", json={"title": "Go"}).status_code == 422
    assert client.post("/courses", json={"title": "FastAPI Basics", "price": -1}).status_code == 422
