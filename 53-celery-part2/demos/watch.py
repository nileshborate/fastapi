# Run: python -m demos.watch       - what are the workers doing? inspect + GET /workers
import asyncio

from app.celery_app import celery_app
from demos.common import flush_redis, log, serve, worker


async def main() -> None:
    flush_redis()
    async with serve() as client:
        response = await client.get("/workers")
        log(f"GET /workers (no worker) -> {response.status_code} {response.json()}")
        with worker(pool="threads", concurrency=4):
            await client.post("/reports/3/pipeline?email=asha@example.com")
            await asyncio.sleep(0.2)                          # the chain is running now
            response = await client.get("/workers")
            log(f"GET /workers -> {response.status_code} {response.json()}")
            inspect = celery_app.control.inspect(timeout=1.0)
            for name, stats in (inspect.stats() or {}).items():
                log(f"stats {name}: pool {stats['pool']['implementation'].split(':')[-1]}, "
                    f"max-concurrency {stats['pool']['max-concurrency']}")
            registered = inspect.registered() or {}
            log(f"registered -> {sorted(next(iter(registered.values())))}")


asyncio.run(main())
