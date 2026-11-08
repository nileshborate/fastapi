from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app import lockout
from app.main import app
from app.sessions import SESSIONS
from app.users import USERS


@pytest.fixture
def client() -> Iterator[TestClient]:
    SESSIONS.clear()                        # every test starts logged out
    lockout.FAILS.clear()                   # homework (Video 36): nobody blocked
    lockout.BLOCKED_UNTIL.clear()
    hashes = {name: user.password_hash for name, user in USERS.items()}
    with TestClient(app) as test_client:
        yield test_client
    for name, password_hash in hashes.items():  # undo password changes
        USERS[name].password_hash = password_hash


def token_for(client: TestClient, username: str, password: str) -> str:
    body = {"username": username, "password": password}
    return client.post("/token/login", json=body).json()["access_token"]


ADMIN = ("nilesh", "admin-pass-123")
STUDENT = ("asha", "student-pass-123")
