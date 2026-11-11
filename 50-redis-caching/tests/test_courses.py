# The cache-aside pattern, invalidation on update, and a Redis that is down
import fakeredis
from fastapi.testclient import TestClient
from redis.asyncio import Redis

from app import db
from app.deps import get_redis
from app.main import app


def test_miss_then_hit(client: TestClient, store: fakeredis.FakeRedis) -> None:
    first = client.get("/courses/3")
    second = client.get("/courses/3")
    assert first.headers["x-cache"] == "MISS"
    assert second.headers["x-cache"] == "HIT"
    assert first.json() == second.json()
    assert db.queries["count"] == 1                          # the database: only once
    assert 55 <= store.ttl("course:3") <= 60                 # it expires by itself


def test_not_found_is_not_cached(client: TestClient, store: fakeredis.FakeRedis) -> None:
    assert client.get("/courses/99").status_code == 404
    assert store.exists("course:99") == 0
    assert client.get("/courses/0").status_code == 422      # validated before the cache


def test_update_deletes_the_cached_copy(client: TestClient, store: fakeredis.FakeRedis) -> None:
    client.get("/courses/1")
    assert store.exists("course:1") == 1
    assert client.patch("/courses/1", json={"price": 699}).status_code == 200
    assert store.exists("course:1") == 0                    # invalidated
    fresh = client.get("/courses/1")
    assert fresh.headers["x-cache"] == "MISS"
    assert fresh.json()["price"] == 699


def test_stats_are_cached_for_30_seconds(client: TestClient) -> None:
    assert client.get("/stats/popular").headers["x-cache"] == "MISS"
    again = client.get("/stats/popular")
    assert again.headers["x-cache"] == "HIT"
    assert 28 <= int(again.headers["x-cache-ttl"]) <= 30
    assert again.json()["top_course"] == "FastAPI Mastery"


def test_health_with_redis(client: TestClient) -> None:
    assert client.get("/health/redis").json() == {"redis": True}


def test_redis_down_the_api_still_works(client: TestClient) -> None:
    dead = Redis.from_url("redis://localhost:6390/0", socket_connect_timeout=0.2)
    app.dependency_overrides[get_redis] = lambda: dead
    response = client.get("/courses/2")
    assert response.status_code == 200
    assert response.headers["x-cache"] == "MISS"
    assert client.get("/health/redis").status_code == 503
