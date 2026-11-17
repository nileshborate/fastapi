# Run: python -m demos.inline      - register a user: the email inside the request vs a task
import asyncio
import time

from demos.common import flush_redis, log, serve, worker


async def main() -> None:
    flush_redis()
    with worker():
        async with serve() as client:
            started = time.perf_counter()
            response = await client.post("/users/register-slow",
                                         json={"email": "asha@example.com", "name": "Asha"})
            log(f"POST /users/register-slow -> {response.status_code} "
                f"in {time.perf_counter() - started:.2f} s   (the email inside the request)")

            started = time.perf_counter()
            response = await client.post("/users/register",
                                         json={"email": "ravi@example.com", "name": "Ravi"})
            body = response.json()
            log(f"POST /users/register      -> {response.status_code} "
                f"in {time.perf_counter() - started:.2f} s   task_id {body['task_id'][:8]}...")

            while True:                                       # what is the worker doing?
                status = (await client.get(f"/tasks/{body['task_id']}")).json()
                log(f"GET /tasks/{body['task_id'][:8]}... -> {status['state']}"
                    + (f"  {status['result']}" if status["result"] else ""))
                if status["state"] in ("SUCCESS", "FAILURE"):
                    break
                await asyncio.sleep(0.5)


asyncio.run(main())
