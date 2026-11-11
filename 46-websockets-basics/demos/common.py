# A REAL server for the demos: uvicorn inside this process, on port 8046
import asyncio
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

PORT = 8046
HTTP = f"http://127.0.0.1:{PORT}"
WS = f"ws://127.0.0.1:{PORT}"
_start = time.perf_counter()


def log(text: str) -> None:
    print(f"{time.perf_counter() - _start:5.2f}s  {text}")


@asynccontextmanager
async def serve(app: FastAPI) -> AsyncIterator[None]:
    global _start
    server = uvicorn.Server(uvicorn.Config(app, port=PORT, log_level="warning"))
    task = asyncio.create_task(server.serve())
    while not server.started:
        await asyncio.sleep(0.05)
    _start = time.perf_counter()                        # the clock starts now
    try:
        yield
    finally:
        server.should_exit = True
        await task
