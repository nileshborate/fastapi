import os

os.environ["API_KEY"] = "test-key"          # set BEFORE the app is imported: real env vars beat .env
os.environ["ENVIRONMENT"] = "test"
os.environ["ALLOWED_HOSTS"] = '["testserver"]'   # the TestClient calls itself "testserver"
os.environ["LOAD_SEED_DATA"] = "false"            # tests start with EMPTY data
os.environ["EMAIL_DELAY_SECONDS"] = "0"          # no waiting in tests
os.environ["LOG_FILE"] = "test-app.log"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"   # tests use their OWN database file

from collections.abc import Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

TEACHER = {"X-API-Key": "test-key", "X-Role": "teacher"}
ADMIN = {"X-API-Key": "test-key", "X-Role": "admin"}


@pytest.fixture
def client() -> Iterator[TestClient]:
    Base.metadata.drop_all(bind=engine)   # a clean database for every test
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:   # "with" runs the lifespan: startup ... shutdown
        yield test_client
    app.dependency_overrides.clear()      # undo any override a test made
