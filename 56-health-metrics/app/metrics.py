# Metrics: numbers over time - Prometheus scrapes GET /metrics every few seconds
import time

from fastapi import Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    disable_created_metrics,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

disable_created_metrics()                           # no extra *_created lines

REQUESTS = Counter("http_requests_total", "HTTP requests", ["method", "route", "status"])
LATENCY = Histogram("http_request_duration_seconds", "Request duration", ["method", "route"],
                    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5))
IN_PROGRESS = Gauge("http_requests_in_progress", "Requests being handled right now")
ENROLLMENTS = Counter("enrollments_total", "New enrollments", ["course"])   # a business metric

SKIP = ("/metrics", "/health")                      # don't measure the measuring


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path.startswith(SKIP):
            return await call_next(request)
        IN_PROGRESS.inc()
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            route = request.scope.get("route")      # the TEMPLATE: /reports/{course_id}
            label = route.path if route else "unmatched"     # never the raw path
            REQUESTS.labels(request.method, label, str(status)).inc()
            LATENCY.labels(request.method, label).observe(time.perf_counter() - start)
            IN_PROGRESS.dec()


def metrics_endpoint() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
