# Run:  pytest -v
import copy
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

import main

# raise_server_exceptions=False -> we see the 500 response instead of the Python error
client = TestClient(main.app, raise_server_exceptions=False)
ORIGINAL = copy.deepcopy(main.COURSES)


@pytest.fixture(autouse=True)
def reset_data() -> Iterator[None]:
    main.COURSES.clear()
    main.COURSES.update(copy.deepcopy(ORIGINAL))
    yield


def test_not_found_has_our_format_and_header() -> None:
    response = client.get("/courses/99")
    assert response.status_code == 404
    assert response.json() == {"error": {"code": "HTTP_404", "message": "Course not found"}}
    assert response.headers["X-Error-Code"] == "COURSE_NOT_FOUND"


def test_dict_detail() -> None:
    response = client.delete("/courses/1")
    assert response.status_code == 403
    assert response.json()["error"]["required_role"] == "admin"


def test_enroll_success() -> None:
    response = client.post("/courses/1/enroll", json={"student": "Asha"})
    assert response.status_code == 201
    assert response.json()["seats_left"] == 1


def test_custom_exception_course_full() -> None:
    response = client.post("/courses/2/enroll", json={"student": "Asha"})
    assert response.status_code == 409
    assert response.json() == {"error": {"code": "COURSE_FULL", "message": "Course 2 has no free seats", "path": "/courses/2/enroll"}}


def test_custom_exception_already_enrolled() -> None:
    client.post("/courses/1/enroll", json={"student": "Asha"})
    assert client.post("/courses/1/enroll", json={"student": "Asha"}).json()["error"]["code"] == "ALREADY_ENROLLED"


def test_validation_errors_are_friendly() -> None:
    response = client.post("/courses/1/enroll", json={"student": "A"})
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["details"][0]["field"] == "student"


def test_unknown_route_uses_same_format() -> None:
    assert client.get("/nope").json() == {"error": {"code": "HTTP_404", "message": "Not Found"}}


def test_crash_returns_safe_500() -> None:
    response = client.get("/crash")
    assert response.status_code == 500
    assert response.json() == {"error": {"code": "INTERNAL_ERROR", "message": "Something went wrong. Please try again."}}
    assert "ZeroDivisionError" not in response.text
