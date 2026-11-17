# REAL servers for the demos: our app on 8056 + a fake payments service on 8057
import asyncio
import os
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI, Response

os.environ.setdefault("DB_PATH", "demo.db")

from app.main import app  # noqa: E402

payments = FastAPI()
payments.state.delay = 0.0                          # the demo makes it slow ...
payments.state.up = True                            # ... or broken


@payments.get("/health")
async def payments_health(response: Response) -> dict[str, str]:
    await asyncio.sleep(payments.state.delay)
    if not payments.state.up:
        response.status_code = 503
    return {"status": "up" if payments.state.up else "down"}


async def _start(asgi: FastAPI, port: int) -> tuple[uvicorn.Server, threading.Thread]:
    server = uvicorn.Server(uvicorn.Config(asgi, port=port, log_level="critical"))   # quiet
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        await asyncio.sleep(0.05)
    return server, thread


@asynccontextmanager
async def serve() -> AsyncIterator[httpx.AsyncClient]:
    running = [await _start(payments, 8057), await _start(app, 8056)]
    try:
        async with httpx.AsyncClient(base_url="http://127.0.0.1:8056", timeout=30) as client:
            yield client
    finally:
        for server, thread in reversed(running):
            server.should_exit = True
            thread.join()
        if os.path.exists("demo.db"):
            os.remove("demo.db")
