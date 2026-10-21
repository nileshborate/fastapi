# Video 5 - send 10 requests at the same time to each endpoint and time them
# Start the server first:   fastapi dev main.py
# Then run:                 python load_test.py

import asyncio
import time

import httpx

BASE = "http://127.0.0.1:8000"


async def hit(path: str, n: int = 10) -> None:
    async with httpx.AsyncClient(base_url=BASE, timeout=60) as client:
        start = time.perf_counter()
        await asyncio.gather(*(client.get(path) for _ in range(n)))
        print(f"{path:<10} {n} requests at once -> {time.perf_counter() - start:4.1f}s")


async def main() -> None:
    await hit("/sync")       # ~1s  (thread pool)
    await hit("/async")      # ~1s  (event loop)
    await hit("/blocking")   # ~10s (event loop blocked!)


asyncio.run(main())
