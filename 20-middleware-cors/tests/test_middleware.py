from fastapi.testclient import TestClient

from tests.conftest import TEACHER

FRONTEND = "http://localhost:3000"


def test_request_id_and_timing_headers(client: TestClient) -> None:
    response = client.get("/")
    assert len(response.headers["X-Request-ID"]) == 32                     # a new uuid4 hex
    assert response.headers["X-Process-Time"].endswith("ms")
    assert response.json()["request_id"] == response.headers["X-Request-ID"]


def test_request_id_from_the_client_is_kept(client: TestClient) -> None:
    response = client.get("/", headers={"X-Request-ID": "abc123"})
    assert response.headers["X-Request-ID"] == "abc123"


def test_middleware_runs_even_for_404(client: TestClient) -> None:
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert "X-Request-ID" in response.headers                             # a dependency would NOT run here


def test_cors_allowed_origin(client: TestClient) -> None:
    response = client.get("/courses", headers={"Origin": FRONTEND})
    assert response.headers["access-control-allow-origin"] == FRONTEND
    assert "X-Request-ID" in response.headers["access-control-expose-headers"]


def test_cors_unknown_origin_gets_no_permission(client: TestClient) -> None:
    response = client.get("/courses", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in response.headers


def test_cors_preflight(client: TestClient) -> None:
    response = client.options(
        "/courses",
        headers={"Origin": FRONTEND, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "X-API-Key"},
    )
    assert response.status_code == 200
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "x-api-key" in response.headers["access-control-allow-headers"].lower()


def test_cors_preflight_from_unknown_origin_fails(client: TestClient) -> None:
    response = client.options("/courses", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "POST"})
    assert response.status_code == 400


def test_gzip_for_big_responses(client: TestClient) -> None:
    for i in range(30):
        client.post("/courses", json={"title": f"A long course title number {i}", "price": 100}, headers=TEACHER)
    response = client.get("/courses", params={"limit": 100}, headers={"Accept-Encoding": "gzip"})
    assert response.headers["content-encoding"] == "gzip"
