# A REAL server for the demos: uvicorn in its OWN thread (with its own event loop), port 8048
# Why a thread? If the server's loop freezes, our client must keep running - and measure it.
import asyncio
import threading
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import uvicorn

from app.main import app

PORT = 8048
HTTP = f"http://127.0.0.1:{PORT}"


async def timed_get(client: httpx.AsyncClient, path: str) -> float:
    start = time.perf_counter()
    response = await client.get(f"{HTTP}{path}")
    response.raise_for_status()
    return time.perf_counter() - start


async def together(client: httpx.AsyncClient, path: str, n: int) -> float:
    """n requests at the SAME time - how long until ALL are answered?"""
    start = time.perf_counter()
    await asyncio.gather(*(client.get(f"{HTTP}{path}") for _ in range(n)))
    return time.perf_counter() - start


@asynccontextmanager
async def serve() -> AsyncIterator[httpx.AsyncClient]:
    server = uvicorn.Server(uvicorn.Config(app, port=PORT, log_level="warning"))
    thread = threading.Thread(target=server.run, name="event-loop", daemon=True)
    thread.start()
    while not server.started:
        await asyncio.sleep(0.05)
    limits = httpx.Limits(max_connections=200)
    try:
        async with httpx.AsyncClient(limits=limits, timeout=60) as client:
            yield client
    finally:
        server.should_exit = True
        thread.join()
