from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app import store
from app.config import get_settings
from app.deprecation import v1_usage
from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    saved = dict(store.COURSES)
    v1_usage.clear()
    with TestClient(app) as test_client:
        yield test_client
    store.COURSES.clear()
    store.COURSES.update(saved)
    get_settings.cache_clear()                     # a test may have changed the sunset
