# Run: python -m demos.down        - Redis is DOWN: the API must still work (just slower)
import asyncio
import os

os.environ["REDIS_URL"] = "redis://localhost:6390/0"       # nothing listens on this port

from demos.common import log, serve  # noqa: E402


async def main() -> None:
    async with serve() as client:
        for _ in range(2):
            response = await client.get("/courses/2")
            log(f"GET /courses/2 -> {response.status_code} {response.headers['x-cache']}  "
                f"{response.json()['title']}")
        response = await client.get("/health/redis")
        log(f"GET /health/redis -> {response.status_code} {response.json()}")


asyncio.run(main())
