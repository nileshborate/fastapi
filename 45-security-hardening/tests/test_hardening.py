# Headers, Host, CORS, HTTPS, /docs and safe errors - development vs production
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def prod_client(base_url: str = "https://api.coursehub.in") -> TestClient:
    app = create_app(Settings(environment="production", allowed_hosts=["api.coursehub.in"],
                              cors_origins=["https://coursehub.in"]))

    async def boom() -> None:
        raise RuntimeError("database password is s3cret!")
    app.add_api_route("/boom", boom)
    return TestClient(app, base_url=base_url, raise_server_exceptions=False)


def test_security_headers(client: TestClient) -> None:
    headers = client.get("/").headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["referrer-policy"] == "no-referrer"
    assert "strict-transport-security" not in headers          # development: no HSTS
    assert client.get("/docs").status_code == 200


def test_production() -> None:
    c = prod_client()
    response = c.get("/")
    assert response.headers["strict-transport-security"].startswith("max-age=31536000")
    assert c.get("/docs").status_code == 404
    assert c.get("/openapi.json").status_code == 404
    crash = c.get("/boom")
    assert crash.status_code == 500 and "s3cret" not in crash.text
    assert crash.json()["detail"] == "Internal server error"
    assert len(crash.json()["error_id"]) == 8


def test_https_host_and_cors() -> None:
    insecure = prod_client("http://api.coursehub.in").get("/", follow_redirects=False)
    assert insecure.status_code == 307
    assert insecure.headers["location"] == "https://api.coursehub.in/"
    assert prod_client("https://evil.example").get("/").status_code == 400
    c = prod_client()
    ask = {"Access-Control-Request-Method": "POST"}
    evil = c.options("/courses", headers=ask | {"Origin": "https://evil.example"})
    assert evil.status_code == 400
    good = c.options("/courses", headers=ask | {"Origin": "https://coursehub.in"})
    assert good.headers["access-control-allow-origin"] == "https://coursehub.in"
