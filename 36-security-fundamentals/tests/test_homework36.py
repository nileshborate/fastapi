# Homework answer (Video 36): change the password, block after 3 wrong passwords
import pytest
from fastapi.testclient import TestClient

from app import lockout
from tests.conftest import STUDENT, token_for


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_change_password(client: TestClient) -> None:
    auth = bearer(token_for(client, *STUDENT))
    wrong = {"old_password": "nope", "new_password": "new-pass-456"}
    assert client.post("/token/password", json=wrong, headers=auth).status_code == 401
    short = {"old_password": STUDENT[1], "new_password": "short"}
    assert client.post("/token/password", json=short, headers=auth).status_code == 422
    good = {"old_password": STUDENT[1], "new_password": "new-pass-456"}
    assert client.post("/token/password", json=good, headers=auth).status_code == 204
    login = {"username": "asha", "password": "new-pass-456"}
    assert client.post("/token/login", json=login).status_code == 200      # the new one
    old = {"username": "asha", "password": STUDENT[1]}
    assert client.post("/token/login", json=old).status_code == 401        # the old one


def test_three_wrong_passwords_block_the_login(client: TestClient,
                                               monkeypatch: pytest.MonkeyPatch) -> None:
    clock = [1000.0]
    monkeypatch.setattr(lockout, "now", lambda: clock[0])
    wrong = {"username": "asha", "password": "nope"}
    for _ in range(3):
        assert client.post("/token/login", json=wrong).status_code == 401
    right = {"username": "asha", "password": STUDENT[1]}
    assert client.post("/token/login", json=right).status_code == 429     # even the right one
    clock[0] += 61                                                        # 61 seconds later
    assert client.post("/token/login", json=right).status_code == 200


def test_a_success_resets_the_count(client: TestClient) -> None:
    wrong = {"username": "asha", "password": "nope"}
    right = {"username": "asha", "password": STUDENT[1]}
    for _ in range(2):
        client.post("/session/login", json=wrong)
    assert client.post("/session/login", json=right).status_code == 200
    client.post("/session/login", json=wrong)
    assert client.post("/session/login", json=right).status_code == 200   # not blocked
