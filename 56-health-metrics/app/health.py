# Liveness: "is the process alive?"   Readiness: "can it serve traffic right now?"
import asyncio
import time
from collections.abc import Awaitable, Callable

import httpx
import redis.asyncio as aioredis
from fastapi import APIRouter, Request, Response

from app import db
from app.config import get_settings

router = APIRouter(prefix="/health", tags=["Health"])
STARTED = time.monotonic()
http = httpx.AsyncClient()                          # ONE client, reused - creating one is slow


async def check_database() -> None:
    def ping() -> None:
        with db.connect() as conn:
            conn.execute("SELECT 1")                # the cheapest real query
    await asyncio.to_thread(ping)                   # sqlite is blocking - not on the loop


async def check_payments() -> None:
    response = await http.get(f"{get_settings().payments_url}/health")
    if response.status_code != 200:
        raise RuntimeError(f"payments answered {response.status_code}")


async def check_redis() -> None:                   # homework 56
    client = aioredis.Redis.from_url(get_settings().redis_url)
    try:
        await client.ping()
    finally:
        await client.aclose()


# name -> (check, critical?)  critical down = NOT ready · non-critical down = degraded
CHECKS: dict[str, tuple[Callable[[], Awaitable[None]], bool]] = {
    "database": (check_database, True),
    "payments": (check_payments, False),
    "redis": (check_redis, True),                   # homework 56: critical
}


async def run_check(check: Callable[[], Awaitable[None]]) -> dict[str, object]:
    start = time.perf_counter()
    try:
        await asyncio.wait_for(check(), timeout=get_settings().check_timeout)
        result: dict[str, object] = {"status": "up"}
    except TimeoutError:
        result = {"status": "down", "error": f"timeout after {get_settings().check_timeout} s"}
    except Exception as exc:
        result = {"status": "down", "error": f"{type(exc).__name__}: {exc}"}
    result["ms"] = round((time.perf_counter() - start) * 1000, 1)
    return result


@router.get("/live")
def live() -> dict[str, str]:
    return {"status": "alive"}                      # NO dependency checks here - ever


@router.get("/ready")
async def ready(request: Request, response: Response) -> dict[str, object]:
    if getattr(request.app.state, "shutting_down", False):
        response.status_code = 503
        return {"status": "draining"}               # stop sending me new requests
    results = await asyncio.gather(*(run_check(check) for check, _ in CHECKS.values()))
    checks = dict(zip(CHECKS, results, strict=True))
    critical = [name for name, (_, is_critical) in CHECKS.items() if is_critical]
    critical_down = any(checks[name]["status"] == "down" for name in critical)
    any_down = any(c["status"] == "down" for c in checks.values())
    status = "not_ready" if critical_down else "degraded" if any_down else "ready"
    if critical_down:
        response.status_code = 503                  # the load balancer skips this instance
    return {"status": status, "version": get_settings().version,
            "uptime_s": round(time.monotonic() - STARTED), "checks": checks}
