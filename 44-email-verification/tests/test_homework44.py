# Homework 44: POST /me/password + the "your password was changed" email
from fastapi.testclient import TestClient

from tests.conftest import ASHA, FakeMailer, login, register


def logged_in(client: TestClient, mailer: FakeMailer) -> dict[str, str]:
    register(client)
    client.post("/verify-email", json={"token": mailer.last_token()})
    token = login(client).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_change_password(client: TestClient, mailer: FakeMailer) -> None:
    headers = logged_in(client, mailer)
    body = {"old_password": "blue-river-42", "new_password": "green-hill-77"}
    assert client.post("/me/password", json=body, headers=headers).status_code == 200
    assert login(client).status_code == 401
    assert login(client, "green-hill-77").status_code == 200
    assert mailer.sent[-1].subject == "Your password was changed"


def test_wrong_old_password_and_no_login(client: TestClient, mailer: FakeMailer) -> None:
    headers = logged_in(client, mailer)
    body = {"old_password": "wrong-password", "new_password": "green-hill-77"}
    response = client.post("/me/password", json=body, headers=headers)
    assert response.status_code == 400 and response.json()["detail"] == "Old password is wrong"
    assert client.post("/me/password", json=body).status_code == 401


def test_a_change_kills_open_reset_links(client: TestClient, mailer: FakeMailer) -> None:
    headers = logged_in(client, mailer)
    client.post("/password/forgot", json={"email": ASHA["email"]})
    reset_token = mailer.last_token()
    body = {"old_password": "blue-river-42", "new_password": "green-hill-77"}
    client.post("/me/password", json=body, headers=headers)
    reset = {"token": reset_token, "new_password": "attacker-pass-1"}
    assert client.post("/password/reset", json=reset).status_code == 400


def test_a_reset_sends_the_email_too(client: TestClient, mailer: FakeMailer) -> None:
    register(client)
    client.post("/password/forgot", json={"email": ASHA["email"]})
    client.post("/password/reset", json={"token": mailer.last_token(),
                                         "new_password": "green-hill-77"})
    assert [e.subject for e in mailer.sent][-1] == "Your password was changed"
