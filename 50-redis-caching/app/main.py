# Video 50 - Caching with Redis, Part 1: cache-aside + TTL
# docker run -d --name redis -p 6379:6379 redis:7-alpine
# fastapi dev app/main.py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.config import get_settings
from app.deps import RedisDep
from app.routers import courses, stats


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.redis = Redis.from_url(get_settings().redis_url, decode_responses=True,
                                     socket_connect_timeout=1, socket_timeout=1)
    yield
    await app.state.redis.aclose()                 # close the connection pool


app = FastAPI(title="Course Hub Cache", version="1.0.0", lifespan=lifespan)
app.include_router(courses.router)
app.include_router(stats.router)


@app.get("/health/redis")
async def redis_health(redis: RedisDep, response: Response) -> dict[str, bool]:
    try:
        ok = await redis.ping()                    # PING -> PONG (True)
    except RedisError:
        ok = False
    if not ok:
        response.status_code = 503                 # the API works - but without its cache
    return {"redis": ok}
