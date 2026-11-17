# A REAL server (uvicorn in its own thread, port 8053) and a REAL Celery worker (a process)
import asyncio
import subprocess
import sys
import threading
import time
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path

import httpx
import uvicorn

from app.main import app

PORT = 8053
HTTP = f"http://127.0.0.1:{PORT}"
_start = time.perf_counter()


def log(text: str) -> None:
    print(f"{time.perf_counter() - _start:5.2f}s  {text}")


def reset_clock() -> None:
    global _start
    _start = time.perf_counter()


@asynccontextmanager
async def serve() -> AsyncIterator[httpx.AsyncClient]:
    server = uvicorn.Server(uvicorn.Config(app, port=PORT, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        await asyncio.sleep(0.05)
    try:
        async with httpx.AsyncClient(base_url=HTTP, timeout=60) as client:
            reset_clock()
            yield client
    finally:
        server.should_exit = True
        thread.join()


def _celery(args: list[str], logfile: str) -> tuple[subprocess.Popen, object]:
    output = open(logfile, "a")
    process = subprocess.Popen([sys.executable, "-m", "celery", "-A", "app.celery_app", *args],
                               stdout=output, stderr=subprocess.STDOUT)
    return process, output


@contextmanager
def worker(pool: str = "solo", concurrency: int = 1, events: bool = False) -> Iterator[None]:
    """a REAL Celery worker in its own process - the same command you type in a terminal"""
    from app.celery_app import celery_app

    process, output = _celery(["worker", f"--pool={pool}", f"--concurrency={concurrency}",
                              "--loglevel=info", "--without-gossip", "--without-mingle",
                              *(["-E"] if events else [])],          # -E: events for Flower
                             "worker.log")
    while not celery_app.control.ping(timeout=0.3):          # wait until it answers
        time.sleep(0.2)
    try:
        yield
    finally:
        process.terminate()
        process.wait()
        output.close()


@contextmanager
def beat() -> Iterator[None]:
    """celery beat: the clock that SENDS scheduled tasks (it never runs them)"""
    process, output = _celery(["beat", "--loglevel=info"], "beat.log")
    try:
        yield
    finally:
        process.terminate()
        process.wait()
        output.close()
        for leftover in Path().glob("celerybeat-schedule*"):     # beat's own small file
            leftover.unlink()


def flush_redis() -> None:
    import redis

    for db in (0, 1):                                         # the queue + the results
        redis.Redis.from_url(f"redis://localhost:6379/{db}").flushdb()
