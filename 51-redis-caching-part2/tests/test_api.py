# The decorated service through the API, invalidation, and the Redis types
import fakeredis
from fastapi.testclient import TestClient

from app import db


def test_decorator_miss_then_hit(client: TestClient, store: fakeredis.FakeRedis) -> None:
    assert client.get("/courses/3").headers["x-cache"] == "MISS"
    second = client.get("/courses/3")
    assert second.headers["x-cache"] == "HIT"
    assert second.json()["title"] == "FastAPI Mastery"
    assert db.queries["count"] == 1
    assert 60 <= store.ttl("course:3") <= 66                # 60 + jitter
    assert client.get("/courses/99").status_code == 404
    assert store.exists("course:99") == 0


def test_patch_invalidates(client: TestClient, store: fakeredis.FakeRedis) -> None:
    client.get("/courses/1")
    client.patch("/courses/1", json={"price": 599})
    assert store.exists("course:1") == 0
    fresh = client.get("/courses/1")
    assert fresh.headers["x-cache"] == "MISS"
    assert fresh.json()["price"] == 599


def test_views_hash_sorted_set_list(client: TestClient, store: fakeredis.FakeRedis) -> None:
    for course_id in [3, 3, 1, 3, 2, 1, 4]:
        assert client.post(f"/courses/{course_id}/views?user=asha").status_code == 204
    assert client.get("/courses/3/stats").json() == {"views": 3, "likes": 0}
    assert client.get("/popular?n=2").json() == [{"course_id": 3, "views": 3},
                                                 {"course_id": 1, "views": 2}]
    assert client.get("/users/asha/recent").json() == [4, 1, 2, 3, 1]   # newest 5
    assert store.llen("recent:asha") == 5


def test_views_validation(client: TestClient) -> None:
    assert client.post("/courses/3/views?user=Asha!").status_code == 422
    assert client.post("/courses/0/views?user=asha").status_code == 422
    assert client.get("/popular?n=11").status_code == 422
