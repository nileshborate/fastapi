# Homework 45: registrations per email domain + Content-Security-Policy
from fastapi.testclient import TestClient

from tests.conftest import PASSWORD


def register(client: TestClient, email: str) -> int:
    body = {"email": email, "full_name": "Test User", "password": PASSWORD}
    return client.post("/users", json=body).status_code


def test_three_accounts_per_domain_per_hour(client: TestClient) -> None:
    codes = [register(client, f"user{n}@spam.example") for n in range(4)]
    assert codes == [201, 201, 201, 429]
    response = client.post("/users", json={"email": "user9@spam.example",
                                           "full_name": "Test User", "password": PASSWORD})
    assert int(response.headers["retry-after"]) > 3500             # about one hour
    assert register(client, "asha@other.example") == 201             # another domain: fine


def test_domain_is_case_insensitive(client: TestClient) -> None:
    for n in range(3):
        register(client, f"user{n}@Spam.Example")
    assert register(client, "user3@SPAM.example") == 429             # emails are lower-cased


def test_content_security_policy(client: TestClient) -> None:
    csp = client.get("/").headers["content-security-policy"]
    assert csp == "default-src 'none'; frame-ancestors 'none'"
    assert "content-security-policy" in client.get("/courses").headers
    assert "content-security-policy" not in client.get("/docs").headers   # Swagger works
    assert "content-security-policy" not in client.get("/redoc").headers
