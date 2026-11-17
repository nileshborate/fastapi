# Part 2: one function for every cache read - with a lock against the stampede - and a decorator
import asyncio
import functools
import inspect
import logging
import random
import typing
import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from typing import Any, TypeVar

from pydantic import TypeAdapter
from redis.asyncio import Redis
from redis.exceptions import RedisError

log = logging.getLogger("cache")
T = TypeVar("T")
cache_status: ContextVar[str] = ContextVar("cache_status", default="SKIP")   # per request

# delete the lock only if it is still OURS (Lua runs inside Redis: check + delete in one step)
RELEASE_LOCK = """
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("DEL", KEYS[1])
end
return 0
"""


def with_jitter(ttl: int, spread: float = 0.1) -> int:
    """60 -> a random number from 60 to 66: keys made together don't expire together"""
    return ttl + random.randint(0, int(ttl * spread))


async def get_or_set(redis: Redis, key: str, ttl: int, loader: Callable[[], Awaitable[T]],
                     adapter: TypeAdapter[T], lock_ttl: int = 5, wait: float = 3.0) -> T:
    lock_key = f"lock:{key}"
    try:
        cached = await redis.get(key)
        if cached is not None:
            cache_status.set("HIT")
            return adapter.validate_json(cached)

        token = uuid.uuid4().hex
        if await redis.set(lock_key, token, nx=True, ex=lock_ttl):    # only ONE request wins
            try:
                cache_status.set("MISS")
                value = await loader()                                # the database - once
                if value is not None:
                    await redis.set(key, adapter.dump_json(value), ex=with_jitter(ttl))
                return value
            finally:
                await redis.eval(RELEASE_LOCK, 1, lock_key, token)

        for _ in range(int(wait / 0.05)):                             # the others wait ...
            await asyncio.sleep(0.05)
            cached = await redis.get(key)
            if cached is not None:
                cache_status.set("WAIT")
                return adapter.validate_json(cached)                  # ... and read the result
            if not await redis.exists(lock_key):
                break                                                 # the winner found nothing
    except RedisError as error:
        log.warning("cache failed: %s", error)
    cache_status.set("SKIP")
    return await loader()                                             # Redis down: the database


def cached(key: str, ttl: int) -> Callable[[Callable[..., Awaitable[Any]]], Any]:
    """@cached("course:{course_id}", ttl=60) - redis must be the first argument"""
    def decorator(func: Callable[..., Awaitable[Any]]) -> Any:
        signature = inspect.signature(func)
        adapter = TypeAdapter(typing.get_type_hints(func)["return"])  # e.g. Course | None

        @functools.wraps(func)
        async def wrapper(redis: Redis, *args: Any, **kwargs: Any) -> Any:
            arguments = signature.bind(redis, *args, **kwargs).arguments
            return await get_or_set(redis, key.format(**arguments), ttl,
                                    lambda: func(redis, *args, **kwargs), adapter)

        async def invalidate(redis: Redis, **arguments: Any) -> None:
            try:
                await redis.delete(key.format(**arguments))
            except RedisError as error:
                log.warning("cache delete failed: %s", error)

        wrapper.invalidate = invalidate                   # get_course.invalidate(redis, ...)
        return wrapper
    return decorator
