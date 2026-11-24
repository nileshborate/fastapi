# The tests talk to a REAL PostgreSQL:  docker compose up -d db
# Always the TEST database (made by db/init) - the tests empty the table before every test.
import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://coursehub:coursehub-dev@127.0.0.1:5432/coursehub_test")


@pytest.fixture
def client() -> Iterator[TestClient]:
    from app import main  # imported here: AFTER DATABASE_URL is set

    with TestClient(main.app) as test_client:
        with main.db.connection() as conn:
            conn.execute("TRUNCATE courses RESTART IDENTITY")     # a clean table, ids from 1
        yield test_client
