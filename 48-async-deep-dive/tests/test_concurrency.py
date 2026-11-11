# Timing tests: 5 requests at the same time, each waits 0.2 s
import asyncio
import time

import httpx
import pytest

pytestmark = pytest.mark.anyio


async def together(client: httpx.AsyncClient, path: str, n: int = 5) -> float:
    start = time.perf_counter()
    responses = await asyncio.gather(*(client.get(path) for _ in range(n)))
    assert all(r.status_code == 200 for r in responses)
    return time.perf_counter() - start


@pytest.mark.parametrize("path", ["/io/async-await", "/io/sync", "/io/offload"])
async def test_waiting_right_runs_together(client: httpx.AsyncClient, path: str) -> None:
    assert await together(client, f"{path}?seconds=0.2") < 0.6       # not 5 x 0.2 = 1.0


async def test_a_blocking_call_in_async_def_runs_one_by_one(client: httpx.AsyncClient) -> None:
    assert await together(client, "/io/async-blocking?seconds=0.2") >= 1.0   # the trap


async def test_who_runs_what(client: httpx.AsyncClient) -> None:
    main = (await client.get("/ping")).json()["thread"]
    assert (await client.get("/io/async-await?seconds=0")).json()["thread"] == main
    assert (await client.get("/io/sync?seconds=0")).json()["thread"] != main   # a worker
    assert (await client.get("/threadpool")).json()["threads"] == 40


async def test_cpu_work_gives_the_same_answer_everywhere(client: httpx.AsyncClient) -> None:
    answers = {(await client.get(f"/cpu/{way}?limit=10000")).json()["primes"]
               for way in ("inline", "thread", "process")}
    assert answers == {1229}                                          # primes below 10,000


async def test_limits_still_apply(client: httpx.AsyncClient) -> None:
    assert (await client.get("/io/sync?seconds=60")).status_code == 422
    assert (await client.get("/cpu/inline?limit=10000000")).status_code == 422
