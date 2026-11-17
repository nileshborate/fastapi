# Run: python -m demos.stampede    - 50 users at the same moment, the key is empty
import asyncio
import time
from collections import Counter

from redis.asyncio import Redis

from app import db
from demos.common import serve


async def burst(client, path: str) -> None:
    db.queries["count"] = 0
    started = time.perf_counter()
    responses = await asyncio.gather(*(client.get(path) for _ in range(50)))
    seconds = time.perf_counter() - started
    states = Counter(r.headers.get("x-cache", "-") for r in responses)
    print(f"{path:17} 50 requests in {seconds:.2f} s   database queries: "
          f"{db.queries['count']:2}   {dict(states) if '-' not in states else ''}")


async def main() -> None:
    redis = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
    await redis.flushdb()
    async with serve() as client:
        print("--- the key is empty, 50 users arrive together")
        await burst(client, "/naive/courses/3")          # Part 1: no lock
        await burst(client, "/courses/3")                # Part 2: a lock - one request loads
        print("--- again: now both keys exist")
        await burst(client, "/naive/courses/3")
        await burst(client, "/courses/3")
        print("TTL course:3       ->", await redis.ttl("course:3"), "s  (60 + jitter)")
    await redis.aclose()


asyncio.run(main())
