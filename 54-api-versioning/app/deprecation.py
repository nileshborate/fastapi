# Every v1 response says: v1 is deprecated, when it ends, and what replaces it
from collections import Counter
from datetime import UTC, datetime
from email.utils import format_datetime

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config import get_settings

v1_usage: Counter[str] = Counter()          # who still calls v1? (a real app: logs + metrics)


class DeprecationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        settings = get_settings()
        v1_usage[request.headers.get("x-client-id", "unknown")] += 1
        successor = "/v2" + request.url.path.removeprefix(request.scope.get("root_path", ""))
        if datetime.now(UTC) >= settings.v1_sunset_at:
            return JSONResponse(status_code=410, content={          # 410 Gone: it was here
                "detail": "API v1 was removed. Please use v2.", "successor": successor})
        response = await call_next(request)
        response.headers["Deprecation"] = f"@{int(settings.v1_deprecated_at.timestamp())}"
        response.headers["Sunset"] = format_datetime(settings.v1_sunset_at, usegmt=True)
        response.headers["Link"] = (f'<{successor}>; rel="successor-version", '
                                    f'<{settings.deprecation_docs}>; rel="deprecation"')
        return response
