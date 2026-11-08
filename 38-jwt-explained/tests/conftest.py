import os

os.environ["JWT_SECRET"] = "test-secret-" + "x" * 40      # tests never use the real one

from collections.abc import Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def login(client: TestClient, email: str, password: str):  # noqa: ANN201
    return client.post("/login", json={"email": email, "password": password})


ASHA = ("asha@example.com", "blue-river-42")
