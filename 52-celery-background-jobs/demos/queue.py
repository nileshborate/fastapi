# Run: python -m demos.queue       - no worker running: the tasks WAIT in Redis, nothing is lost
import asyncio

import redis

from demos.common import flush_redis, log, serve, worker


async def main() -> None:
    flush_redis()
    queue = redis.Redis.from_url("redis://localhost:6379/0")
    async with serve() as client:
        ids = []
        for name in ["Asha", "Ravi", "Meera"]:
            user = {"email": f"{name.lower()}@example.com", "name": name}
            response = await client.post("/users/register", json=user)
            ids.append(response.json()["task_id"])
        log(f"3 users registered -> {response.status_code} (no worker is running)")
        log(f"LLEN celery -> {queue.llen('celery')}   (3 tasks waiting in the Redis list)")
        states = [(await client.get(f"/tasks/{i}")).json()["state"] for i in ids]
        log(f"states -> {states}")

        log("start the worker ...")
        with worker(wait=False):
            last = states
            while True:
                states = [(await client.get(f"/tasks/{i}")).json()["state"] for i in ids]
                if states != last:                                # print only changes
                    log(f"states -> {states}   LLEN celery -> {queue.llen('celery')}")
                    last = states
                if all(state == "SUCCESS" for state in states):
                    break
                await asyncio.sleep(0.1)
        unknown = (await client.get("/tasks/00000000-0000-0000-0000-000000000000")).json()
        log(f"an id that never existed -> {unknown['state']}   (!)")


asyncio.run(main())
