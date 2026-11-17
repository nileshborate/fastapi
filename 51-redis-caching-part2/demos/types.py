# Run: python -m demos.types       - a hash, a sorted set, a list - and a pipeline
import asyncio
import time

from redis.asyncio import Redis


async def main() -> None:
    redis = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
    await redis.flushdb()

    print("--- HASH: many fields under one key")
    await redis.hset("course:3:stats", mapping={"views": 0, "likes": 0})
    await redis.hincrby("course:3:stats", "views", 5)
    await redis.hincrby("course:3:stats", "likes", 2)
    print("HGETALL course:3:stats ->", await redis.hgetall("course:3:stats"))

    print("--- SORTED SET: members sorted by a score")
    for course_id, views in [(1, 40), (2, 15), (3, 90), (4, 25)]:
        await redis.zadd("courses:popular", {str(course_id): views})
    await redis.zincrby("courses:popular", 30, "2")
    print("top 3 ->", await redis.zrange("courses:popular", 0, 2, desc=True, withscores=True))

    print("--- LIST: the newest first, keep only 5")
    for course_id in [1, 2, 3, 4, 2, 1, 3]:
        await redis.lpush("recent:asha", course_id)
        await redis.ltrim("recent:asha", 0, 4)
    print("LRANGE recent:asha 0 -1 ->", await redis.lrange("recent:asha", 0, -1))

    print("--- PIPELINE: 1,000 INCR")
    started = time.perf_counter()
    for _ in range(1000):
        await redis.incr("one-by-one")
    print(f"one by one:    {time.perf_counter() - started:.3f} s   (1,000 round trips)")
    started = time.perf_counter()
    async with redis.pipeline(transaction=False) as pipe:
        for _ in range(1000):
            pipe.incr("pipelined")
        results = await pipe.execute()
    print(f"in a pipeline: {time.perf_counter() - started:.3f} s   (1 round trip)"
          f"   last result: {results[-1]}")
    await redis.aclose()


asyncio.run(main())
