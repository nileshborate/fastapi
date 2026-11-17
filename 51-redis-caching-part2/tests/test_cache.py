# get_or_set: the lock against the stampede, the jitter, Redis down - tested without a server
import asyncio

import fakeredis
import pytest
from pydantic import TypeAdapter
from redis.asyncio import Redis

from app.cache import get_or_set, with_jitter

pytestmark = pytest.mark.anyio
NUMBER = TypeAdapter(int)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def counting_loader(calls: list[int], delay: float = 0.2):
    async def loader() -> int:
        calls.append(1)
        await asyncio.sleep(delay)                      # a slow database query
        return 42
    return loader


async def test_fifty_at_once_one_query(server: fakeredis.FakeServer) -> None:
    redis = fakeredis.FakeAsyncRedis(server=server, decode_responses=True)
    calls: list[int] = []
    loader = counting_loader(calls)
    values = await asyncio.gather(*(get_or_set(redis, "n", 60, loader, NUMBER)
                                    for _ in range(50)))
    assert values == [42] * 50
    assert len(calls) == 1                              # the lock: only one request loads
    assert await redis.exists("lock:n") == 0            # and the lock is gone again


async def test_a_none_is_not_cached(server: fakeredis.FakeServer) -> None:
    redis = fakeredis.FakeAsyncRedis(server=server, decode_responses=True)

    async def nothing() -> int | None:
        return None

    assert await get_or_set(redis, "x", 60, nothing, TypeAdapter(int | None)) is None
    assert await redis.exists("x") == 0


async def test_redis_down_uses_the_loader() -> None:
    dead = Redis.from_url("redis://localhost:6390/0", socket_connect_timeout=0.2)
    calls: list[int] = []
    assert await get_or_set(dead, "n", 60, counting_loader(calls, 0), NUMBER) == 42
    assert len(calls) == 1


def test_jitter_stays_in_range() -> None:
    values = {with_jitter(60) for _ in range(500)}
    assert min(values) >= 60 and max(values) <= 66
    assert len(values) > 1                              # really random
