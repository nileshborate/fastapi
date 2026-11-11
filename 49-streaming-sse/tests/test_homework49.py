# Homework 49: the clock (SSE) and resuming JSON Lines
import json
import time

from fastapi.testclient import TestClient

from tests.conftest import sse_events


def test_clock_ticks_then_done(client: TestClient) -> None:
    started = time.perf_counter()
    response = client.get("/clock?count=3&interval=0.1")
    assert time.perf_counter() - started >= 0.3                    # one tick per interval
    events = sse_events(response.text)
    assert [e["event"] for e in events] == ["tick", "tick", "tick", "done"]
    first = json.loads(events[0]["data"])
    assert first["n"] == 1 and len(first["time"]) == 8              # "HH:MM:SS"


def test_clock_count_is_limited(client: TestClient) -> None:
    assert client.get("/clock?count=0").status_code == 422
    assert client.get("/clock?count=61").status_code == 422


def test_lessons_resume_after(client: TestClient) -> None:
    response = client.get("/lessons/stream?count=2&delay=0&after=3")
    ids = [json.loads(line)["id"] for line in response.text.splitlines()]
    assert ids == [4, 5]
