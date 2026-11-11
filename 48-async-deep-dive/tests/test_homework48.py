# Homework 48: a blocking report that doesn't freeze /ping + a threadpool of 10
import asyncio
import time
from collections.abc import AsyncIterator

import httpx
import pytest

import app.main
from app.main import app as fastapi_app
from app.main import lifespan

pytestmark = pytest.mark.anyio


async def timed(client: httpx.AsyncClient, path: str) -> float:
    start = time.perf_counter()
    assert (await client.get(path)).status_code == 200
    return time.perf_counter() - start


async def test_reports_dont_freeze_ping(client: httpx.AsyncClient) -> None:
    reports = [asyncio.create_task(client.get(f"/reports/{n}")) for n in range(1, 6)]
    await asyncio.sleep(0.1)                                   # 5 reports are running
    assert await timed(client, "/ping") < 0.1
    answers = await asyncio.gather(*reports)
    assert [r.json()["report"] for r in answers] == [1, 2, 3, 4, 5]


@pytest.fixture
async def small_pool(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[httpx.AsyncClient]:
    monkeypatch.setattr(app.main, "THREADS", 10)               # the lifespan reads it
    async with lifespan(fastapi_app):
        transport = httpx.ASGITransport(app=fastapi_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


async def test_a_threadpool_of_10(small_pool: httpx.AsyncClient) -> None:
    assert (await small_pool.get("/threadpool")).json()["threads"] == 10

    async def together(n: int) -> float:
        start = time.perf_counter()
        await asyncio.gather(*(small_pool.get("/io/sync?seconds=0.3") for _ in range(n)))
        return time.perf_counter() - start

    assert await together(10) < 0.55                          # one round
    assert await together(11) >= 0.6                          # the 11th waits: two rounds
