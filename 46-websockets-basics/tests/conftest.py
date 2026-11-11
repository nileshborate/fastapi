from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.manager import manager


@pytest.fixture
def client() -> Iterator[TestClient]:
    manager.active.clear()                          # every test starts with an empty class
    with TestClient(app) as test_client:
        yield test_client
