# Run:  pytest -v
from typing import Any

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

VALID: dict[str, Any] = {
    "title": "FastAPI Basics",
    "price": 999,
    "start_date": "2026-11-01",
    "end_date": "2026-11-30",
    "instructor": {"name": "Nilesh Borate", "email": "nilesh@example.com"},
    "lessons": [{"title": "Intro", "minutes": 15}, {"title": "Routes", "minutes": 25}],
}


def post(**changes: Any) -> Any:
    return client.post("/courses", json={**VALID, **changes})


def first_error(**changes: Any) -> dict[str, Any]:
    response = post(**changes)
    assert response.status_code == 422
    error: dict[str, Any] = response.json()["detail"][0]
    return error


def test_valid_course() -> None:
    response = post()
    assert response.status_code == 201
    assert response.json()["total_minutes"] == 40
    assert response.json()["start_date"] == "2026-11-01"


def test_title_not_all_caps() -> None:
    assert first_error(title="FASTAPI BASICS")["msg"] == "Value error, title must not be ALL CAPS"


def test_tags_are_cleaned() -> None:
    assert post(tags=[" FastAPI", "python", "fastapi "]).json()["tags"] == ["fastapi", "python"]


def test_tags_from_text() -> None:
    assert post(tags="Python, FastAPI").json()["tags"] == ["fastapi", "python"]


def test_end_before_start() -> None:
    error = first_error(end_date="2026-10-01")
    assert error["loc"] == ["body"]
    assert "end_date must be on or after start_date" in error["msg"]


def test_discount_must_be_lower() -> None:
    assert "discount_price" in first_error(discount_price=999)["msg"]


def test_nested_error_location() -> None:
    error = first_error(instructor={"name": "Nilesh", "email": "wrong"})
    assert error["loc"] == ["body", "instructor", "email"]


def test_list_item_error_location() -> None:
    error = first_error(lessons=[{"title": "Intro", "minutes": 15}, {"title": "Routes", "minutes": 0}])
    assert error["loc"] == ["body", "lessons", 1, "minutes"]


def test_whitespace_is_stripped() -> None:
    assert post(title="   FastAPI Basics   ").json()["title"] == "FastAPI Basics"


def test_extra_fields_forbidden() -> None:
    assert first_error(teacher="Nilesh")["type"] == "extra_forbidden"
