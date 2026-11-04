import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"       # tests use their OWN database file

from collections.abc import Iterator  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


@pytest.fixture
def alembic_cfg() -> Config:
    return Config(str(ALEMBIC_INI))                       # the same config as the "alembic" command


@pytest.fixture
def client(alembic_cfg: Config) -> Iterator[TestClient]:
    command.downgrade(alembic_cfg, "base")                # an EMPTY database ...
    command.upgrade(alembic_cfg, "head")                  # ... built by OUR migrations - not create_all
    with TestClient(app) as test_client:
        yield test_client
