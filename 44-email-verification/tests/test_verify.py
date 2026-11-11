# Register -> email -> verify (once) -> log in
from fastapi.testclient import TestClient

from tests.conftest import ASHA, FakeMailer, login, register


def test_register_sends_one_email(client: TestClient, mailer: FakeMailer) -> None:
    response = register(client)
    assert response.status_code == 201 and response.json()["is_verified"] is False
    assert len(mailer.sent) == 1
    email = mailer.sent[0]
    assert email.to == "asha@example.com" and email.subject == "Confirm your email"
    assert "http://localhost:3000/verify-email?token=" in email.body


def test_verify_then_login(client: TestClient, mailer: FakeMailer) -> None:
    register(client)
    assert login(client).status_code == 403                      # not verified yet
    token = mailer.last_token()
    response = client.post("/verify-email", json={"token": token})
    assert response.status_code == 200 and response.json()["is_verified"] is True
    assert login(client).status_code == 200
    again = client.post("/verify-email", json={"token": token})
    assert again.status_code == 400 and again.json()["detail"] == "Invalid or expired link"


def test_wrong_password_is_still_401(client: TestClient) -> None:
    register(client)
    assert login(client, "wrong-password").status_code == 401   # not "verify first"


def test_resend_kills_the_old_link(client: TestClient, mailer: FakeMailer) -> None:
    register(client)
    first = mailer.last_token()
    answer = client.post("/verify-email/resend", json={"email": ASHA["email"]})
    assert answer.status_code == 202 and len(mailer.sent) == 2
    assert client.post("/verify-email", json={"token": first}).status_code == 400
    second = mailer.last_token()
    assert client.post("/verify-email", json={"token": second}).status_code == 200
    client.post("/verify-email/resend", json={"email": ASHA["email"]})
    assert len(mailer.sent) == 2                                  # verified: no more emails


def test_garbage_and_duplicate(client: TestClient) -> None:
    register(client)
    assert client.post("/verify-email", json={"token": "x" * 43}).status_code == 400
    assert register(client).status_code == 409
