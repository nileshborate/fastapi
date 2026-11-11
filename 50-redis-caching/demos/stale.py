# Run: python -m demos.stale       - old data in the cache: TTL, and deleting the key on update
import asyncio
import os

os.environ["COURSE_TTL"] = "3"                     # a short TTL, so we can watch it expire

from redis.asyncio import Redis  # noqa: E402

from app import db  # noqa: E402
from demos.common import log, serve  # noqa: E402


async def show(client, note: str = "") -> None:
    response = await client.get("/courses/1")
    log(f"GET /courses/1 -> {response.headers['x-cache']:4} price {response.json()['price']}"
        f"  {note}")


async def main() -> None:
    redis = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
    await redis.flushdb()
    async with serve() as client:
        await show(client)
        await show(client)
        log(f"TTL course:1 -> {await redis.ttl('course:1')} s")

        log("another program changes the price in the DATABASE to 599 (no cache delete)")
        db.COURSES[1] = db.COURSES[1].model_copy(update={"price": 599})
        await show(client, "<- STALE: the old copy")
        await asyncio.sleep(3.1)
        await show(client, "<- the TTL ended: fresh")

        response = await client.patch("/courses/1", json={"price": 699})
        log(f"PATCH /courses/1 price=699 -> {response.status_code} (database + DELETE key)")
        log(f"EXISTS course:1 -> {await redis.exists('course:1')}")
        await show(client, "<- fresh at once")
        await show(client)

        stats = await client.get("/stats/popular")
        log(f"GET /stats/popular -> {stats.headers['x-cache']}  {stats.json()}")
        await asyncio.sleep(1)
        stats = await client.get("/stats/popular")
        log(f"GET /stats/popular -> {stats.headers['x-cache']}  "
            f"X-Cache-TTL: {stats.headers['x-cache-ttl']} s")
    await redis.aclose()


asyncio.run(main())
