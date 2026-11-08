# Logout of one device, and logout everywhere
from fastapi.testclient import TestClient

from tests.conftest import bearer, login, refresh


def test_logout_kills_the_refresh_token(client: TestClient) -> None:
    pair = login(client)
    body = {"refresh_token": pair["refresh_token"]}
    assert client.post("/logout", json=body).status_code == 204
    response = refresh(client, pair["refresh_token"])
    assert response.status_code == 401 and response.json()["detail"] == "Refresh token revoked"
    # the access token still works until it expires - that's the price of stateless JWTs
    assert client.get("/me", headers=bearer(pair)).status_code == 200


def test_logout_never_fails(client: TestClient) -> None:
    pair = login(client)
    body = {"refresh_token": pair["refresh_token"]}
    assert client.post("/logout", json=body).status_code == 204
    assert client.post("/logout", json=body).status_code == 204          # twice: fine
    assert client.post("/logout", json={"refresh_token": "garbage"}).status_code == 204


def test_logout_everywhere(client: TestClient) -> None:
    phone, laptop = login(client), login(client)
    assert len(client.get("/me/sessions", headers=bearer(phone)).json()) == 2
    assert client.post("/logout/all", headers=bearer(laptop)).status_code == 204
    assert client.get("/me", headers=bearer(phone)).status_code == 401    # "ver" is old
    assert refresh(client, phone["refresh_token"]).status_code == 401
    fresh = login(client)                                                 # log in again
    assert client.get("/me", headers=bearer(fresh)).status_code == 200
    assert len(client.get("/me/sessions", headers=bearer(fresh)).json()) == 1


def test_logout_all_needs_a_login(client: TestClient) -> None:
    assert client.post("/logout/all").status_code == 401
