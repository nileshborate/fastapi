# Video 65/66 - what Prometheus reads from us every 15 s: GET /metrics (never public: nginx)
import os
import time

from fastapi import Request, Response
from prometheus_client import (  # Video 66: 2 workers
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    multiprocess,
)
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

REQUESTS = Counter("http_requests_total", "HTTP requests, by route and status",
                   ["method", "route", "status"])
LATENCY = Histogram("http_request_duration_seconds", "Time to answer, by route",
                    ["method", "route"],    # homework 65: up to 10 s - past the pool timeout
                    buckets=(.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 7.5, 10))
IN_PROGRESS = Gauge("http_requests_in_progress", "Requests being answered right now",
                    multiprocess_mode="livesum")     # Video 66: the sum over all workers
APP_INFO = Gauge("coursehub_info", "Always 1 - the labels say which version runs",
                 ["version", "commit"], multiprocess_mode="max")


def route_of(request: Request) -> str:
    """the route TEMPLATE (/courses/{course_id}), never the path (/courses/7): one series per
    route - not one per id, and not one per random URL a scanner tries (all 'unmatched')"""
    route = request.scope.get("route")
    return getattr(route, "path", "unmatched")


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path == "/metrics":               # don't measure the measuring
            return await call_next(request)
        IN_PROGRESS.inc()
        start = time.perf_counter()
        status = 500                                     # an exception = a 500 for the user
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            IN_PROGRESS.dec()
            route = route_of(request)
            LATENCY.labels(request.method, route).observe(time.perf_counter() - start)
            REQUESTS.labels(request.method, route, str(status)).inc()


def metrics() -> Response:
    # Video 66: 2 workers = 2 processes, each with its OWN counters. A scrape reaches ONE of
    # them - so every worker writes into PROMETHEUS_MULTIPROC_DIR, and we add them all up
    if os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
