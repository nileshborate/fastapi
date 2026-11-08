# Login -> a JWT -> GET /me with "Authorization: Bearer <token>"
from fastapi.testclient import TestClient

from tests.conftest import ASHA, login


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_login_returns_a_jwt(client: TestClient) -> None:
    body = login(client, *ASHA).json()
    assert body["token_type"] == "bearer" and body["expires_in"] == 900
    assert body["access_token"].count(".") == 2


def test_wrong_password(client: TestClient) -> None:
    response = login(client, "asha@example.com", "nope")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_me(client: TestClient) -> None:
    token = login(client, *ASHA).json()["access_token"]
    me = client.get("/me", headers=bearer(token)).json()
    assert me["email"] == "asha@example.com" and me["role"] == "student"


def test_me_without_or_with_a_bad_token(client: TestClient) -> None:
    assert client.get("/me").json() == {"detail": "Not authenticated"}
    token = login(client, *ASHA).json()["access_token"]
    header, payload, signature = token.split(".")
    response = client.get("/me", headers=bearer(f"{header}.{payload}x.{signature}"))
    assert response.status_code == 401
    assert response.json()["detail"].startswith("Invalid token")
