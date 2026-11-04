import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"       # tests use their OWN database file

from collections.abc import Iterator  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed  # noqa: E402

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


@pytest.fixture
def client() -> Iterator[TestClient]:
    cfg = Config(str(ALEMBIC_INI))
    command.downgrade(cfg, "base")                        # an EMPTY database ...
    command.upgrade(cfg, "head")                          # ... built by our migrations
    with SessionLocal() as db:
        seed(db)                                          # ... + the SAME demo data every time
    with TestClient(app) as test_client:
        yield test_client
