# Run: python -m demos.retry       - a flaky email server: retries with backoff and a limit
import asyncio

from demos.common import flush_redis, log, reset_clock, serve, worker


async def follow(client, to: str) -> None:
    reset_clock()
    response = await client.post("/emails", json={"to": to})
    log(f"POST /emails {to} -> {response.status_code}")
    last = None
    while True:
        status = (await client.get(response.headers["location"])).json()
        if status["state"] != last:                           # print only changes
            detail = status["result"] or status["error"] or ""
            log(f"   {status['state']:8} {detail}")
            last = status["state"]
        if status["state"] in ("SUCCESS", "FAILURE"):
            break
        await asyncio.sleep(0.05)


async def main() -> None:
    flush_redis()
    with worker():
        async with serve() as client:
            await follow(client, "asha@example.com")         # fails 2x, then works
            await follow(client, "bounce@example.com")       # a permanent error
            await follow(client, "down@example.com")         # the server stays down


asyncio.run(main())
