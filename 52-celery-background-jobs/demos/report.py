# Run: python -m demos.report      - 202 Accepted, progress from the worker, and a failure
import asyncio

from demos.common import flush_redis, log, serve, worker


async def follow(client, course_id: int) -> None:
    response = await client.post(f"/reports/{course_id}")
    log(f"POST /reports/{course_id} -> {response.status_code}  "
        f"Location: {response.headers['location'][:15]}...")
    last = None
    while True:
        status = (await client.get(response.headers["location"])).json()
        shown = status["state"] + (f" {status['progress']}" if status["progress"] else "")
        if shown != last:                                     # print only changes
            log(f"   {shown}" + (f"  {status['result']}" if status["result"] else "")
                + (f"  {status['error']}" if status["error"] else ""))
            last = shown
        if status["state"] in ("SUCCESS", "FAILURE"):
            break
        await asyncio.sleep(0.1)


async def main() -> None:
    flush_redis()
    with worker():
        async with serve() as client:
            await follow(client, 3)
            await follow(client, 99)


asyncio.run(main())
