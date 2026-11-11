# JSON Lines and Server-Sent Events
import json

from fastapi.testclient import TestClient

from app.routers import live
from tests.conftest import sse_events


def test_json_lines(client: TestClient) -> None:
    response = client.get("/lessons/stream?count=3&delay=0")
    assert response.headers["content-type"] == "application/jsonl"
    lessons = [json.loads(line) for line in response.text.splitlines()]
    assert [lesson["id"] for lesson in lessons] == [1, 2, 3]


def test_progress_events(client: TestClient) -> None:
    response = client.get("/jobs/export-1/progress?delay=0")
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["cache-control"] == "no-cache"
    events = sse_events(response.text)
    assert [e["id"] for e in events[:-1]] == ["1", "2", "3", "4", "5"]
    assert json.loads(events[2]["data"])["percent"] == 60
    assert events[-1] == {"event": "done", "data": "[DONE]"}
    assert "export-1: stopped after step 5" in live.cleanups     # finally ran


def test_resume_with_last_event_id(client: TestClient) -> None:
    response = client.get("/jobs/export-1/progress?delay=0", headers={"Last-Event-ID": "3"})
    ids = [e.get("id") for e in sse_events(response.text)]
    assert ids == ["4", "5", None]                               # 4, 5 and "done"


def test_chat_over_post(client: TestClient) -> None:
    response = client.post("/chat/stream", json={"text": "Hi"})
    tokens = [json.loads(e["data"]) for e in sse_events(response.text) if e["event"] == "token"]
    assert " ".join(tokens).startswith("You asked: Hi")
    assert client.post("/chat/stream", json={"text": ""}).status_code == 422


def test_a_bad_job_name(client: TestClient) -> None:
    assert client.get("/jobs/Bad%20Name/progress").status_code == 422
