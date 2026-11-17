# Two versions of one API: shapes, shared data, deprecation, sunset, header versioning
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

V2 = "application/vnd.coursehub.v2+json"


def test_v1_shape_never_changes(client: TestClient) -> None:
    assert client.get("/v1/courses/2").json() == {
        "id": 2, "name": "SQL Joins", "teacher": "Asha", "price": 299}


def test_v2_shape(client: TestClient) -> None:
    assert client.get("/v2/courses/2").json() == {
        "id": 2, "title": "SQL Joins", "teacher": {"name": "Asha"},
        "price": {"amount": "299.50", "currency": "INR"}, "tags": ["sql"]}


def test_one_store_for_both_versions(client: TestClient) -> None:
    created = client.post("/v1/courses", json={"name": "Git", "teacher": "Meera",
                                              "price": 199}).json()
    assert client.get(f"/v2/courses/{created['id']}").json()["price"]["amount"] == "199.00"
    body = {"title": "Docker 101", "teacher": {"name": "Ravi"}, "price": {"amount": "399.99"}}
    created = client.post("/v2/courses", json=body).json()
    assert client.get(f"/v1/courses/{created['id']}").json()["price"] == 399


def test_validation_per_version(client: TestClient) -> None:
    assert client.post("/v2/courses", json={"title": "Git", "teacher": {"name": "Meera"},
                                            "price": {"amount": "1.999"}}).status_code == 422
    assert client.post("/v1/courses", json={"title": "Git"}).status_code == 422


def test_only_v1_is_deprecated(client: TestClient) -> None:
    v1 = client.get("/v1/courses/1")
    assert v1.headers["deprecation"] == "@1793491200"            # 2026-11-01 00:00 UTC
    assert v1.headers["sunset"] == "Sat, 01 May 2027 00:00:00 GMT"
    assert '</v2/courses/1>; rel="successor-version"' in v1.headers["link"]
    assert "deprecation" not in client.get("/v2/courses/1").headers


def test_after_the_sunset_v1_is_gone(client: TestClient,
                                     monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("V1_SUNSET_AT", "2026-01-01T00:00:00Z")
    from app.config import get_settings
    get_settings.cache_clear()
    assert get_settings().v1_sunset_at < datetime.now(UTC)
    response = client.get("/v1/courses/1")
    assert response.status_code == 410
    assert response.json()["successor"] == "/v2/courses/1"
    assert client.get("/v2/courses/1").status_code == 200


def test_separate_docs(client: TestClient) -> None:
    v1 = client.get("/v1/openapi.json").json()
    v2 = client.get("/v2/openapi.json").json()
    assert (v1["info"]["version"], v2["info"]["version"]) == ("1.0.0", "2.0.0")
    assert v1["paths"]["/courses"]["get"]["deprecated"] is True
    assert "deprecated" not in v2["paths"]["/courses"]["get"]


def test_header_versioning(client: TestClient) -> None:
    assert "name" in client.get("/courses/1").json()                  # default: v1
    response = client.get("/courses/1", headers={"Accept": V2})
    assert response.json()["title"] == "Python Basics"
    assert response.headers["vary"] == "Accept"


def test_v1_usage(client: TestClient) -> None:
    client.get("/v1/courses", headers={"X-Client-Id": "android-3.1"})
    client.get("/v1/courses", headers={"X-Client-Id": "android-3.1"})
    client.get("/v1/courses")
    assert client.get("/admin/v1-usage").json() == {"android-3.1": 2, "unknown": 1}
