import asyncio
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from app import health
from app.config import get_settings
from app.main import app


async def payments_up() -> None:                    # no network in the tests
    return None


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setattr(get_settings(), "db_path", str(tmp_path / "test.db"))
    monkeypatch.setitem(health.CHECKS, "payments", (payments_up, False))
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def metric() -> Callable[..., float]:
    """the current value of one series - counters only go up, so tests compare before/after"""
    return lambda name, **labels: REGISTRY.get_sample_value(name, labels) or 0.0


async def payments_down() -> None:
    raise ConnectionError("payments is down")


async def payments_hangs() -> None:
    await asyncio.sleep(5)
