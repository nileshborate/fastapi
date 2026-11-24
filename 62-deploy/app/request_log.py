# Homework 61.2: one JSON line per request in the api's log - with nginx's request id
# (a small version of Video 55: nginx makes the id, sends it as X-Request-ID, we log it)
import json
import logging
import sys
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

log = logging.getLogger("app.http")
if not log.handlers:                                   # stdout -> docker compose logs api
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    log.propagate = False


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # behind nginx: its $request_id. Called directly (tests, curl :8000): our own one
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.request_id = request_id
        start = time.perf_counter()
        response = await call_next(request)
        log.info(json.dumps({"event": "request.done", "request_id": request_id,
                             "method": request.method, "path": request.url.path,
                             "status": response.status_code,
                             "duration_ms": round((time.perf_counter() - start) * 1000, 1)}))
        return response
