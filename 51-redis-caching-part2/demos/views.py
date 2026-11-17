# Run: python -m demos.views       - views through the API: counters, a leaderboard, recent
import asyncio

from redis.asyncio import Redis

from demos.common import serve

VIEWS = [("asha", 3), ("ravi", 3), ("asha", 1), ("meera", 3), ("ravi", 2), ("asha", 4),
         ("asha", 3), ("meera", 1), ("asha", 2), ("asha", 5), ("ravi", 3), ("asha", 1)]


async def main() -> None:
    redis = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
    await redis.flushdb()
    async with serve() as client:
        for user, course_id in VIEWS:
            response = await client.post(f"/courses/{course_id}/views?user={user}")
        print(f"12 x POST /courses/{{id}}/views -> {response.status_code}")
        print("GET /courses/3/stats    ->", (await client.get("/courses/3/stats")).json())
        print("GET /popular            ->", (await client.get("/popular")).json())
        print("GET /users/asha/recent  ->", (await client.get("/users/asha/recent")).json())
        bad = await client.post("/courses/3/views?user=Asha!")
        print("POST ...?user=Asha!     ->", bad.status_code)
    await redis.aclose()


asyncio.run(main())
