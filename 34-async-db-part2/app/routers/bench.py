# Four ways to wait - measured in demos/benchmark.py
import asyncio
import time

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

router = APIRouter(prefix="/bench", tags=["Benchmark"])

DELAY = 0.1     # pretend: a slow database, or a slow API - 100 ms


def slow_report() -> str:
    """A normal (sync) library function - we can't change it, we can't await it."""
    time.sleep(DELAY)
    return "report ready"


@router.get("/sync")
def bench_sync() -> dict[str, str]:
    time.sleep(DELAY)                           # def: runs in the thread pool - OK
    return {"mode": "sync"}


@router.get("/async")
async def bench_async() -> dict[str, str]:
    await asyncio.sleep(DELAY)                  # await: the event loop serves others - OK
    return {"mode": "async"}


@router.get("/blocking")
async def bench_blocking() -> dict[str, str]:
    time.sleep(DELAY)                           # WRONG: blocks the whole event loop
    return {"mode": "blocking"}


@router.get("/threadpool")
async def bench_threadpool() -> dict[str, str]:
    report = await run_in_threadpool(slow_report)   # the sync call goes to a thread
    return {"mode": "threadpool", "report": report}


# ---------------------------------------------------------------- homework answer (Video 34)
REPORT_DELAY = 0.2


def make_report() -> dict[str, str]:
    """A sync function that takes 0.2 s - e.g. a PDF library."""
    time.sleep(REPORT_DELAY)
    return {"report": "ready"}


@router.get("/report")
async def bench_report() -> dict[str, str]:
    return await run_in_threadpool(make_report)     # the event loop stays free
