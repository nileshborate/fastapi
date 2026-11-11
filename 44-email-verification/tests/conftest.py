import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["JWT_SECRET"] = "test-secret-" + "x" * 40

import re  # noqa: E402
from collections.abc import Iterator  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from alembic import command  # noqa: E402
from app.mailer import Email, get_mailer  # noqa: E402
from app.main import app  # noqa: E402

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


class FakeMailer:
    """remembers every email - tests read the links from here"""

    def __init__(self) -> None:
        self.sent: list[Email] = []

    def send(self, email: Email) -> None:
        self.sent.append(email)

    def last_token(self) -> str:
        return re.search(r"token=([\w-]+)", self.sent[-1].body).group(1)


@pytest.fixture
def mailer() -> FakeMailer:
    return FakeMailer()


@pytest.fixture
def client(mailer: FakeMailer) -> Iterator[TestClient]:
    cfg = Config(str(ALEMBIC_INI))
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    app.dependency_overrides[get_mailer] = lambda: mailer      # no real emails in tests
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


ASHA = {"email": "asha@example.com", "full_name": "Asha Patil", "password": "blue-river-42"}


def register(client: TestClient, user: dict = ASHA):
    return client.post("/users", json=user)


def login(client: TestClient, password: str = "blue-river-42", email: str = ASHA["email"]):
    return client.post("/token", data={"username": email, "password": password})
