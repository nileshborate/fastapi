import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from collections.abc import AsyncIterator  # noqa: E402
from pathlib import Path  # noqa: E402

import httpx  # noqa: E402
import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402

from app.database import engine  # noqa: E402
from app.main import app  # noqa: E402

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def fresh_db() -> None:
    cfg = Config(str(ALEMBIC_INI))
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")


@pytest.fixture
async def api(fresh_db: None) -> AsyncIterator[httpx.AsyncClient]:
    # NEW: an ASYNC test client - the app runs on the test's own event loop
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    await engine.dispose()          # close the connections of THIS event loop


async def add_school(api: httpx.AsyncClient) -> None:
    await api.post("/teachers", json={"name": "Nilesh"})
    for title, fee in (("FastAPI Basics", 299), ("Docker Deep Dive", 499),
                       ("Git in One Hour", 99), ("AWS for Developers", 799)):
        await api.post("/courses", json={"title": title, "fee": fee, "teacher_id": 1})
