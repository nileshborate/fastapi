# One request id per request, a log line per request, and a JSON 500 with the id
import logging
import time
import uuid

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.logging_setup import request_id_var

log = logging.getLogger("app.http")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        token = request_id_var.set(request_id)          # every log line from now on has it
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception:
            log.exception("request.failed")             # level ERROR + the traceback
            response = JSONResponse({"detail": "Internal server error",
                                     "request_id": request_id}, status_code=500)
        finally:
            log.info("request.done", extra={
                "method": request.method, "path": request.url.path, "status": status,
                "duration_ms": round((time.perf_counter() - start) * 1000, 1)})
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = request_id   # the client can quote it to support
        return response
