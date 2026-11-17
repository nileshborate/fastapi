# Run: python -m demos.canvas      - a chain (one after another) and a chord (parallel + join)
import asyncio

from demos.common import flush_redis, log, reset_clock, serve, worker


async def wait_for(client, response) -> None:
    while True:
        status = (await client.get(response.headers["location"])).json()
        if status["state"] in ("SUCCESS", "FAILURE"):
            log(f"   {status['state']}  {status['result']}")
            return
        await asyncio.sleep(0.05)


async def main() -> None:
    flush_redis()
    with worker(pool="threads", concurrency=4):             # 4 tasks at the same time
        async with serve() as client:
            reset_clock()
            response = await client.post("/reports/3/pipeline?email=asha@example.com")
            log(f"chain: load -> make_report -> notify   {response.status_code}")
            await wait_for(client, response)                  # 3 steps x 0.5 s

            reset_clock()
            response = await client.post("/reports/summary?course_ids=1&course_ids=2"
                                         "&course_ids=3")
            log(f"chord: 3 x load_course in parallel -> summarize   {response.status_code}")
            await wait_for(client, response)                  # 3 x 0.5 s, together

            response = await client.post("/reports/summary?course_ids=9")
            log(f"summary of course 9 -> {response.status_code} {response.json()}")


asyncio.run(main())
