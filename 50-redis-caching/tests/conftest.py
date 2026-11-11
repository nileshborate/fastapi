import os

os.environ["DB_DELAY"] = "0"                       # no slow "database" in the tests

from collections.abc import Iterator  # noqa: E402

import fakeredis  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import db  # noqa: E402
from app.deps import get_redis  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def server() -> fakeredis.FakeServer:
    return fakeredis.FakeServer()                  # one in-memory "Redis server" per test


@pytest.fixture
def store(server: fakeredis.FakeServer) -> fakeredis.FakeRedis:
    """a SYNC client on the same fake server: the test looks inside the cache with it"""
    return fakeredis.FakeRedis(server=server, decode_responses=True)


@pytest.fixture
def client(server: fakeredis.FakeServer) -> Iterator[TestClient]:
    fake = fakeredis.FakeAsyncRedis(server=server, decode_responses=True)
    app.dependency_overrides[get_redis] = lambda: fake
    saved = dict(db.COURSES)
    db.queries["count"] = 0
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    db.COURSES.clear()
    db.COURSES.update(saved)
