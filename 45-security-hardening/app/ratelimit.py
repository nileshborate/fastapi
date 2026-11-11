# Rate limiting: at most N requests per window - per client, per action
import math
import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import HTTPException, Request, status


class RateLimiter:
    """a sliding window: remember WHEN each request came, forget the ones that are too old"""

    def __init__(self, limit: int, seconds: float,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self.limit = limit
        self.seconds = seconds
        self.clock = clock                              # tests can pass a fake clock
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = self.clock()
        hits = self.hits[key]
        while hits and hits[0] <= now - self.seconds:   # older than the window: forget
            hits.popleft()
        if len(hits) >= self.limit:
            retry = math.ceil(hits[0] + self.seconds - now)
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                                detail="Too many requests - try again later",
                                headers={"Retry-After": str(retry)})
        hits.append(now)

    def reset(self) -> None:
        self.hits.clear()


def client_ip(request: Request) -> str:
    # behind a proxy: start uvicorn with --proxy-headers --forwarded-allow-ips=<the proxy>
    return request.client.host if request.client else "unknown"
