# Run: python -m demos.frozen
# One slow request is running. How long does a tiny GET /ping take now?
import asyncio

from demos.common import serve, timed_get


async def ping_during(client, slow_path: str) -> None:
    slow = asyncio.create_task(timed_get(client, slow_path))
    await asyncio.sleep(0.1)                              # the slow request is running now
    ping = await timed_get(client, "/ping")
    await slow
    print(f"{'during ' + slow_path:<37} GET /ping took {ping:5.2f} s")


async def main() -> None:
    async with serve() as client:
        alone = await timed_get(client, "/ping")
        print(f"{'nothing else running':<37} GET /ping took {alone:5.2f} s")
        await ping_during(client, "/io/async-await?seconds=2")
        await ping_during(client, "/io/sync?seconds=2")
        await ping_during(client, "/io/async-blocking?seconds=2")
        await ping_during(client, "/cpu/inline?limit=400000")


if __name__ == "__main__":
    asyncio.run(main())
