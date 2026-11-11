# Small helpers: the key names in ONE place - and a cache that may fail without breaking the API
import logging

from redis.asyncio import Redis
from redis.exceptions import RedisError

log = logging.getLogger("cache")


def course_key(course_id: int) -> str:
    return f"course:{course_id}"                     # "type:id" - easy to read and to delete


async def cache_get(redis: Redis, key: str) -> str | None:
    try:
        return await redis.get(key)
    except RedisError as error:                      # Redis is down? -> just a MISS
        log.warning("cache get failed: %s", error)
        return None


async def cache_set(redis: Redis, key: str, value: str, ttl: int) -> None:
    try:
        await redis.set(key, value, ex=ttl)          # SET key value EX ttl
    except RedisError as error:
        log.warning("cache set failed: %s", error)


async def cache_delete(redis: Redis, key: str) -> None:
    try:
        await redis.delete(key)
    except RedisError as error:
        log.warning("cache delete failed: %s", error)
