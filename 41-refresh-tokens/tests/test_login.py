# Login hands out a PAIR - and the two tokens can never be swapped
import jwt
from fastapi.testclient import TestClient

from tests.conftest import bearer, login, refresh


def test_login_returns_a_pair(client: TestClient) -> None:
    pair = login(client)
    assert set(pair) == {"access_token", "refresh_token", "token_type", "expires_in"}
    assert pair["token_type"] == "bearer" and pair["expires_in"] == 900
    access = jwt.decode(pair["access_token"], options={"verify_signature": False})
    refresh_claims = jwt.decode(pair["refresh_token"], options={"verify_signature": False})
    assert access["type"] == "access" and access["ver"] == 0
    assert refresh_claims["type"] == "refresh" and len(refresh_claims["jti"]) == 36
    assert refresh_claims["exp"] - refresh_claims["iat"] == 7 * 24 * 3600
    assert client.get("/me", headers=bearer(pair)).status_code == 200


def test_a_refresh_token_is_not_an_access_token(client: TestClient) -> None:
    pair = login(client)
    wrong = {"Authorization": f"Bearer {pair['refresh_token']}"}
    assert client.get("/me", headers=wrong).status_code == 401


def test_an_access_token_cannot_refresh(client: TestClient) -> None:
    pair = login(client)
    response = refresh(client, pair["access_token"])
    assert response.status_code == 401 and response.json()["detail"] == "Invalid refresh token"


def test_wrong_password(client: TestClient) -> None:
    login(client)
    form = {"username": "asha@example.com", "password": "wrong-password"}
    assert client.post("/token", data=form).status_code == 401
