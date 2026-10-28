# Middleware = code that runs for EVERY request (before the endpoint) and response (after it).
import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Request, Response

CallNext = Callable[[Request], Awaitable[Response]]


async def request_id_and_timing(request: Request, call_next: CallNext) -> Response:
    # 1. BEFORE the endpoint
    request_id = request.headers.get("X-Request-ID") or uuid4().hex
    request.state.request_id = request_id          # endpoints can read it
    start = time.perf_counter()

    # 2. pass the request on - to the next middleware, and finally to the endpoint
    response = await call_next(request)

    # 3. AFTER the endpoint
    ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{ms:.1f}ms"
    path = request.url.path
    print(f"[{request_id[:8]}] {request.method} {path} -> {response.status_code} ({ms:.1f} ms)")
    return response
