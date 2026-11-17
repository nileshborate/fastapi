# Homework 51: one like per user (a Redis set) and a cached leaderboard
import fakeredis
from fastapi.testclient import TestClient


def test_one_like_per_user(client: TestClient, store: fakeredis.FakeRedis) -> None:
    assert client.post("/courses/3/likes?user=asha").json() == {"new": True, "likes": 1}
    assert client.post("/courses/3/likes?user=asha").json() == {"new": False, "likes": 1}
    assert client.post("/courses/3/likes?user=ravi").json() == {"new": True, "likes": 2}
    assert store.smembers("course:3:likers") == {"asha", "ravi"}
    assert client.get("/courses/3/stats").json() == {"views": 0, "likes": 2}
    assert client.post("/courses/3/likes?user=Asha!").status_code == 422


def test_leaderboard_is_cached(client: TestClient, store: fakeredis.FakeRedis) -> None:
    client.post("/courses/2/views?user=asha")
    first = client.get("/popular?n=2")
    assert first.json() == [{"course_id": 2, "views": 1}]
    assert 10 <= store.ttl("popular:2") <= 11                      # 10 s + jitter
    client.post("/courses/4/views?user=asha")
    assert client.get("/popular?n=2").json() == [{"course_id": 2, "views": 1}]   # 10 s old
    store.delete("popular:2")
    assert len(client.get("/popular?n=2").json()) == 2             # fresh after the TTL
