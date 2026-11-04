# Run: python -m demos.benchmark  - 50 requests at the same time, against each endpoint
import asyncio
import time

import httpx

from app.main import app

REQUESTS = 50


async def measure(client: httpx.AsyncClient, path: str) -> float:
    start = time.perf_counter()
    responses = await asyncio.gather(*(client.get(path) for _ in range(REQUESTS)))
    assert all(r.status_code == 200 for r in responses)
    return time.perf_counter() - start


async def main() -> None:
    transport = httpx.ASGITransport(app=app)    # calls the app directly - no server needed
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        print(f"{REQUESTS} requests at once, each one waits 0.1 s:")
        for path in ("/bench/sync", "/bench/async", "/bench/blocking", "/bench/threadpool"):
            print(f"  {path:<17} {await measure(client, path):5.2f} s")


if __name__ == "__main__":
    asyncio.run(main())
