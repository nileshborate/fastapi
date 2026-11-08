# Homework answer (Video 34): teacher summary with gather, a sync report without blocking
import asyncio
import time

import httpx
import pytest

from tests.conftest import add_school

pytestmark = pytest.mark.anyio


async def test_teacher_summary(api: httpx.AsyncClient) -> None:
    await add_school(api)
    assert (await api.get("/teachers/1/summary")).json() == {
        "id": 1, "name": "Nilesh", "courses": 4, "total_fees": 1696,
    }
    assert (await api.get("/teachers/9/summary")).status_code == 404


async def test_summary_without_courses(api: httpx.AsyncClient) -> None:
    await api.post("/teachers", json={"name": "Asha"})
    body = (await api.get("/teachers/1/summary")).json()
    assert body["courses"] == 0 and body["total_fees"] == 0


async def test_report_does_not_block(api: httpx.AsyncClient) -> None:
    start = time.perf_counter()
    responses = await asyncio.gather(*(api.get("/bench/report") for _ in range(20)))
    elapsed = time.perf_counter() - start
    assert all(r.json() == {"report": "ready"} for r in responses)
    assert elapsed < 20 * 0.2 / 4                   # 4.0 s if blocking - here about 0.2 s
