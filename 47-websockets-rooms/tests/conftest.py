import os
from collections.abc import Iterator

os.environ.setdefault("JWT_SECRET", "test-secret-test-secret-test-secret-123")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.rooms import rooms  # noqa: E402
from app.users import PASSWORD  # noqa: E402


@pytest.fixture
def client() -> Iterator[TestClient]:
    rooms.rooms.clear()
    with TestClient(app) as test_client:
        yield test_client


def token(client: TestClient, username: str) -> str:
    form = {"username": username, "password": PASSWORD}
    return client.post("/token", data=form).json()["access_token"]
