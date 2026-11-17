# Homework 52: a reminder (404 before queueing) and one report for several courses
import pytest
from fastapi.testclient import TestClient

from app.tasks import send_reminder


def test_reminder_for_a_known_user(client: TestClient) -> None:
    client.post("/users/register", json={"email": "asha@example.com", "name": "Asha"})
    response = client.post("/users/asha@example.com/reminder")
    assert response.status_code == 202
    status = client.get(f"/tasks/{response.json()['task_id']}").json()
    assert status["state"] == "SUCCESS"
    assert status["result"]["to"] == "asha@example.com"


def test_reminder_unknown_user_is_not_queued(client: TestClient,
                                             monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    monkeypatch.setattr(send_reminder, "delay", lambda *args: calls.append(args))
    assert client.post("/users/nobody@example.com/reminder").status_code == 404
    assert calls == []                                       # nothing went to the queue
    assert client.post("/users/not-an-email/reminder").status_code == 422


def test_multi_report(client: TestClient) -> None:
    response = client.post("/reports?course_ids=1&course_ids=3")
    assert response.status_code == 202
    status = client.get(response.headers["location"]).json()
    assert status["state"] == "SUCCESS"
    assert [r["title"] for r in status["result"]] == ["Python Basics", "FastAPI Mastery"]
    assert client.post("/reports").status_code == 422        # at least one course
