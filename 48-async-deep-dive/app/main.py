# Video 48 - Async Deep Dive: def vs async def, the event loop, the threadpool, blocking calls
import asyncio
import multiprocessing
import os
from collections.abc import AsyncIterator
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager

from anyio import to_thread
from fastapi import FastAPI

from app.routers import cpu, io, reports
from app.work import count_primes, thread_name

THREADS = int(os.environ.get("THREADS", "40"))          # homework 48: the threadpool size


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    to_thread.current_default_thread_limiter().total_tokens = THREADS   # homework 48
    spawn = multiprocessing.get_context("spawn")          # fresh processes - like on Windows
    with ProcessPoolExecutor(max_workers=2, mp_context=spawn) as pool:
        loop = asyncio.get_running_loop()                 # warm up: start both processes now
        await asyncio.gather(*(loop.run_in_executor(pool, count_primes, 10) for _ in range(2)))
        app.state.process_pool = pool                     # CPU work: separate processes
        yield


app = FastAPI(title="Course Hub - Async Deep Dive", version="1.0.0", lifespan=lifespan)
app.include_router(io.router)
app.include_router(cpu.router)
app.include_router(reports.router)                          # homework 48


@app.get("/ping")
async def ping() -> dict[str, str]:
    """answers instantly - IF the event loop is free"""
    return {"ping": "pong", "thread": thread_name()}


@app.get("/threadpool")
async def threadpool() -> dict[str, int]:
    limiter = to_thread.current_default_thread_limiter()
    return {"threads": int(limiter.total_tokens), "busy": limiter.borrowed_tokens}
