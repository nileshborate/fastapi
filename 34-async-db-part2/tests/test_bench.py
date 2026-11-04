# Measured in a test: 50 requests at the same time
import asyncio
import time

import httpx
import pytest

from app.routers import bench

pytestmark = pytest.mark.anyio
REQUESTS = 50


async def timed(api: httpx.AsyncClient, path: str) -> float:
    start = time.perf_counter()
    responses = await asyncio.gather(*(api.get(path) for _ in range(REQUESTS)))
    assert all(r.status_code == 200 for r in responses)
    return time.perf_counter() - start


@pytest.fixture
def short_delay(monkeypatch: pytest.MonkeyPatch) -> float:
    monkeypatch.setattr(bench, "DELAY", 0.05)       # keep the test fast
    return 0.05


async def test_async_waits_together(api: httpx.AsyncClient, short_delay: float) -> None:
    assert await timed(api, "/bench/async") < 10 * short_delay       # not 50 x


async def test_sync_uses_the_thread_pool(api: httpx.AsyncClient, short_delay: float) -> None:
    assert await timed(api, "/bench/sync") < 10 * short_delay        # 40 threads


async def test_blocking_runs_one_by_one(api: httpx.AsyncClient, short_delay: float) -> None:
    assert await timed(api, "/bench/blocking") >= REQUESTS * short_delay * 0.9


async def test_threadpool_fixes_it(api: httpx.AsyncClient, short_delay: float) -> None:
    assert await timed(api, "/bench/threadpool") < 10 * short_delay
    assert (await api.get("/bench/threadpool")).json()["report"] == "report ready"
