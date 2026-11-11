# Waiting (I/O): the right way and the wrong way, in async def and in def
import asyncio
import time
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.concurrency import run_in_threadpool

from app.work import slow_report, thread_name

router = APIRouter(prefix="/io", tags=["Waiting (I/O)"])

Seconds = Annotated[float, Query(ge=0, le=5)]


@router.get("/async-await")
async def async_await(seconds: Seconds = 0.5) -> dict[str, str]:
    """GOOD: await gives the event loop back while we wait"""
    await asyncio.sleep(seconds)
    return {"endpoint": "async def + await", "thread": thread_name()}


@router.get("/async-blocking")
async def async_blocking(seconds: Seconds = 0.5) -> dict[str, str]:
    """BAD: a blocking call inside async def - the WHOLE server waits"""
    time.sleep(seconds)                                  # no await: the event loop is stuck
    return {"endpoint": "async def + time.sleep", "thread": thread_name()}


@router.get("/sync")
def sync_endpoint(seconds: Seconds = 0.5) -> dict[str, str]:
    """GOOD: a plain def - FastAPI runs it in the threadpool"""
    time.sleep(seconds)                                  # blocks only this worker thread
    return {"endpoint": "def + time.sleep", "thread": thread_name()}


@router.get("/offload")
async def offload(seconds: Seconds = 0.5) -> dict[str, str]:
    """GOOD: async def, but the blocking part goes to the threadpool"""
    report = await run_in_threadpool(slow_report, seconds)
    return {"endpoint": "async def + run_in_threadpool", "thread": thread_name(),
            "report": report}
