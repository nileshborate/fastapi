# Middleware = code that runs for EVERY request (before the endpoint) and response (after it).
import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse

from app.config import get_settings

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


async def security_headers(request: Request, call_next: CallNext) -> Response:   # homework (Video 20)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"     # don't guess the content type
    response.headers["X-Frame-Options"] = "DENY"               # never show us inside an <iframe>
    response.headers["Referrer-Policy"] = "no-referrer"        # don't send our URL to other sites
    return response


async def limit_upload_size(request: Request, call_next: CallNext) -> Response:  # homework (Video 20)
    max_mb = get_settings().max_upload_mb
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > max_mb * 1024 * 1024:
        return JSONResponse(                                   # stop here: call_next is NOT called
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            content={"detail": f"Request too large. Max {max_mb} MB"},
        )
    return await call_next(request)
