# Homework 50: the cached list, PATCH deletes it too, and a cache-clear endpoint
import fakeredis
from fastapi.testclient import TestClient

from app import db


def test_list_is_cached(client: TestClient, store: fakeredis.FakeRedis) -> None:
    first = client.get("/courses")
    second = client.get("/courses")
    assert first.headers["x-cache"] == "MISS"
    assert second.headers["x-cache"] == "HIT"
    assert len(second.json()) == 4
    assert db.queries["count"] == 1
    assert 55 <= store.ttl("courses:all") <= 60


def test_patch_deletes_the_list_too(client: TestClient, store: fakeredis.FakeRedis) -> None:
    client.get("/courses")
    client.patch("/courses/2", json={"price": 349})
    assert store.exists("courses:all") == 0
    fresh = client.get("/courses")
    assert fresh.headers["x-cache"] == "MISS"
    assert {c["id"]: c["price"] for c in fresh.json()}[2] == 349


def test_clear_one_course(client: TestClient, store: fakeredis.FakeRedis) -> None:
    client.get("/courses/3")
    assert store.exists("course:3") == 1
    response = client.delete("/cache/courses/3")
    assert response.status_code == 204
    assert response.content == b""
    assert store.exists("course:3") == 0
    assert client.delete("/cache/courses/0").status_code == 422
