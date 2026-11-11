# A REAL server for the demos: uvicorn in its own thread, port 8050
import asyncio
import threading
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import uvicorn

from app.main import app

PORT = 8050
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
