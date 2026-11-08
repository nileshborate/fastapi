from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.sessions import SESSIONS


@pytest.fixture
def client() -> Iterator[TestClient]:
    SESSIONS.clear()                        # every test starts logged out
    with TestClient(app) as test_client:
        yield test_client


def token_for(client: TestClient, username: str, password: str) -> str:
    body = {"username": username, "password": password}
    return client.post("/token/login", json=body).json()["access_token"]


ADMIN = ("nilesh", "admin-pass-123")
STUDENT = ("asha", "student-pass-123")
