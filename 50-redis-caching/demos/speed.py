# Run: python -m demos.speed       - the same course, read 20 times: with and without the cache
import asyncio
import time

from redis.asyncio import Redis

from app import db
from demos.common import serve


async def read(client, course_id: int = 3) -> tuple[str, float]:
    started = time.perf_counter()
    response = await client.get(f"/courses/{course_id}")
    return response.headers["x-cache"], (time.perf_counter() - started) * 1000


async def main() -> None:
    redis = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
    await redis.flushdb()
    async with serve() as client:

        print("--- 20 reads of /courses/3, one after another")
        db.queries["count"] = 0
        started = time.perf_counter()
        for n in range(1, 21):
            state, ms = await read(client)
            if n <= 3 or n == 20:
                print(f"request {n:2}: {state:4}  {ms:6.1f} ms")
        total = time.perf_counter() - started
        print(f"with the cache:    {total:.2f} s   database queries: {db.queries['count']}")

        db.queries["count"] = 0
        started = time.perf_counter()
        for _ in range(20):
            await redis.delete("course:3")             # as if there were no cache
            await read(client)
        total = time.perf_counter() - started
        print(f"without the cache: {total:.2f} s   database queries: {db.queries['count']}")

        print("--- 50 users at the SAME moment, the key just expired")
        await redis.delete("course:3")
        db.queries["count"] = 0
        results = await asyncio.gather(*(read(client) for _ in range(50)))
        misses = sum(state == "MISS" for state, _ in results)
        print(f"MISS: {misses} of 50   database queries: {db.queries['count']}"
              "   <- a cache stampede (Part 2)")
    await redis.aclose()


asyncio.run(main())
