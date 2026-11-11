# A REAL server for the demos: uvicorn inside this process, on port 8047
import asyncio
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import uvicorn

from app.main import app
from app.users import PASSWORD

PORT = 8047
HTTP = f"http://127.0.0.1:{PORT}"
WS = f"ws://127.0.0.1:{PORT}"
_start = time.perf_counter()


def log(text: str) -> None:
    print(f"{time.perf_counter() - _start:5.2f}s  {text}")


async def login(client: httpx.AsyncClient, username: str) -> str:
    form = {"username": username, "password": PASSWORD}
    return (await client.post(f"{HTTP}/token", data=form)).json()["access_token"]


@asynccontextmanager
async def serve() -> AsyncIterator[httpx.AsyncClient]:
    global _start
    server = uvicorn.Server(uvicorn.Config(app, port=PORT, log_level="warning"))
    task = asyncio.create_task(server.serve())
    while not server.started:
        await asyncio.sleep(0.05)
    _start = time.perf_counter()
    try:
        async with httpx.AsyncClient() as client:
            yield client
    finally:
        server.should_exit = True
        await task
