# Video 5 - def vs async def in FastAPI
# Run:   fastapi dev main.py
# Then in another terminal:   python load_test.py

import asyncio
import time

from fastapi import FastAPI

app = FastAPI()


@app.get("/sync")
def sync_endpoint() -> dict[str, str]:
    time.sleep(1)                 # blocking, but OK: FastAPI runs "def" in a thread pool
    return {"type": "def + time.sleep"}


@app.get("/async")
async def async_endpoint() -> dict[str, str]:
    await asyncio.sleep(1)        # non-blocking: the event loop serves others meanwhile
    return {"type": "async def + await asyncio.sleep"}


@app.get("/blocking")
async def blocking_endpoint() -> dict[str, str]:
    time.sleep(1)                 # MISTAKE: blocks the whole event loop!
    return {"type": "async def + time.sleep (bad)"}
