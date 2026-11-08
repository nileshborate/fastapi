# POST /token - the OAuth2 password flow
from fastapi.testclient import TestClient

from tests.conftest import get_token


def test_login_with_a_form(client: TestClient) -> None:
    form = {"username": "asha@example.com", "password": "blue-river-42"}
    response = client.post("/token", data=form)                 # data= : a form
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer" and body["access_token"].count(".") == 2


def test_email_in_any_case(client: TestClient) -> None:
    assert get_token(client, username="ASHA@Example.com")


def test_wrong_password_and_unknown_email(client: TestClient) -> None:
    for form in ({"username": "asha@example.com", "password": "nope"},
                 {"username": "nobody@example.com", "password": "blue-river-42"}):
        response = client.post("/token", data=form)
        assert response.status_code == 401
        assert response.json() == {"detail": "Incorrect email or password"}
        assert response.headers["www-authenticate"] == "Bearer"


def test_json_is_not_the_password_flow(client: TestClient) -> None:
    form = {"username": "asha@example.com", "password": "blue-river-42"}
    assert client.post("/token", json=form).status_code == 422


def test_grant_type_must_be_password_if_sent(client: TestClient) -> None:
    form = {"username": "asha@example.com", "password": "blue-river-42",
            "grant_type": "client_credentials"}
    assert client.post("/token", data=form).status_code == 422
