# Run: python -m demos.basics     (first: docker run -d --name redis -p 6379:6379 redis:7-alpine)
# Redis on its own: keys, values, and keys that expire by themselves
import asyncio

from redis.asyncio import Redis


async def main() -> None:
    redis = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
    await redis.flushdb()                                          # a clean demo database

    print("SET greeting hello      ->", await redis.set("greeting", "hello"))
    print("GET greeting            ->", await redis.get("greeting"))
    print("TTL greeting            ->", await redis.ttl("greeting"), "  (-1: no expiry)")
    print("GET missing             ->", await redis.get("missing"))
    print("TTL missing             ->", await redis.ttl("missing"), "  (-2: no such key)")

    print("SET otp:asha 4821 EX 2  ->", await redis.set("otp:asha", "4821", ex=2))
    print("TTL otp:asha            ->", await redis.ttl("otp:asha"))
    await asyncio.sleep(2.1)
    print("2.1 s later: GET        ->", await redis.get("otp:asha"), "  (gone by itself)")

    for _ in range(3):
        visits = await redis.incr("visits:home")                   # atomic counter
    print("INCR visits:home x3     ->", visits)
    print("KEYS *                  ->", sorted(await redis.keys("*")), "  (not in production)")
    print("DEL greeting            ->", await redis.delete("greeting"))

    raw = Redis.from_url("redis://localhost:6379/0")               # no decode_responses
    await raw.set("greeting", "hello")
    print("without decode_responses ->", await raw.get("greeting"))
    await raw.aclose()
    await redis.aclose()


asyncio.run(main())
