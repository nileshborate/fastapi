# Computing (CPU): threads don't help in Python - other PROCESSES do
import asyncio
from typing import Annotated

from fastapi import APIRouter, Query, Request
from fastapi.concurrency import run_in_threadpool

from app.work import count_primes

router = APIRouter(prefix="/cpu", tags=["Computing (CPU)"])

Limit = Annotated[int, Query(ge=2, le=2_000_000)]


@router.get("/inline")
async def inline(limit: Limit = 200_000) -> dict[str, int]:
    """BAD: heavy math in async def - the event loop is busy computing"""
    return {"primes": count_primes(limit)}


@router.get("/thread")
async def in_thread(limit: Limit = 200_000) -> dict[str, int]:
    """the loop stays free - but the GIL lets only ONE thread run Python at a time"""
    return {"primes": await run_in_threadpool(count_primes, limit)}


@router.get("/process")
async def in_process(request: Request, limit: Limit = 200_000) -> dict[str, int]:
    """GOOD for CPU: another process, with its own Python and its own GIL"""
    loop = asyncio.get_running_loop()
    pool = request.app.state.process_pool
    return {"primes": await loop.run_in_executor(pool, count_primes, limit)}
