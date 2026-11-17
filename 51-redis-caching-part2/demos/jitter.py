# Run: python -m demos.jitter      - 6 keys cached at the same second: when do they expire?
import asyncio

from redis.asyncio import Redis

from app.cache import with_jitter


async def main() -> None:
    redis = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
    await redis.flushdb()
    for n in range(1, 7):
        await redis.set(f"plain:{n}", "x", ex=60)
        await redis.set(f"jitter:{n}", "x", ex=with_jitter(60))
    plain = [await redis.ttl(f"plain:{n}") for n in range(1, 7)]
    jitter = [await redis.ttl(f"jitter:{n}") for n in range(1, 7)]
    print("ex=60              ->", plain, "  all together")
    print("ex=with_jitter(60) ->", jitter, "  spread out")
    await redis.aclose()


asyncio.run(main())
