# Tokens: the server remembers nothing - 401 vs 403
from fastapi.testclient import TestClient

from tests.conftest import ADMIN, STUDENT, token_for


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_login_and_me(client: TestClient) -> None:
    token = token_for(client, *STUDENT)
    assert client.get("/token/me", headers=bearer(token)).json() == {
        "username": "asha", "role": "student"}


def test_no_token_is_401(client: TestClient) -> None:
    response = client.get("/token/me")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_changed_token_is_401(client: TestClient) -> None:
    token = token_for(client, *STUDENT)
    response = client.get("/token/me", headers=bearer(token.replace(".", "x.", 1)))
    assert response.json() == {"detail": "Invalid signature"}


def test_authentication_vs_authorization(client: TestClient) -> None:
    assert client.get("/admin/stats").status_code == 401                 # who are you?
    student = token_for(client, *STUDENT)
    assert client.get("/admin/stats", headers=bearer(student)).status_code == 403   # no
    admin = token_for(client, *ADMIN)
    assert client.get("/admin/stats", headers=bearer(admin)).json() == {
        "users": 2, "checked_by": "nilesh"}
