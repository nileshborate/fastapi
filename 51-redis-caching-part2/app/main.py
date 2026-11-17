# Video 51 - Caching with Redis, Part 2: the stampede, a cache decorator, more Redis types
# docker run -d --name redis -p 6379:6379 redis:7-alpine
# fastapi dev app/main.py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from app.config import get_settings
from app.routers import courses, naive, views


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.redis = Redis.from_url(get_settings().redis_url, decode_responses=True,
                                     socket_connect_timeout=1, socket_timeout=1)
    yield
    await app.state.redis.aclose()


app = FastAPI(title="Course Hub Cache 2", version="1.0.0", lifespan=lifespan)
app.include_router(courses.router)
app.include_router(views.router)
app.include_router(naive.router)
