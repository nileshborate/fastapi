# Retries, the canvas, the schedule and the worker endpoint
from typing import Any

import pytest
from celery.schedules import crontab
from fastapi.testclient import TestClient

from app import email_server
from app.celery_app import celery_app
from app.tasks import send_email


def status_of(client: TestClient, response: Any) -> dict[str, Any]:
    return client.get(response.headers["location"]).json()


def test_retry_until_it_works(client: TestClient) -> None:
    response = client.post("/emails", json={"to": "asha@example.com"})
    assert response.status_code == 202
    status = status_of(client, response)
    assert status["state"] == "SUCCESS"
    assert status["result"] == {"to": "asha@example.com", "attempts": 3}   # 2 fails + 1


def test_permanent_error_is_not_retried(client: TestClient) -> None:
    status = status_of(client, client.post("/emails", json={"to": "bounce@example.com"}))
    assert status["state"] == "FAILURE"
    assert "invalid address" in status["error"]
    assert "bounce@example.com" not in email_server.attempts      # failed before trying


def test_give_up_after_max_retries(client: TestClient) -> None:
    status = status_of(client, client.post("/emails", json={"to": "down@example.com"}))
    assert status["state"] == "FAILURE"
    assert email_server.attempts["down@example.com"] == 4          # 1 try + 3 retries


def test_retry_settings() -> None:
    assert send_email.max_retries == 3
    assert send_email.autoretry_for == (email_server.EmailServerDown,)


def test_chain(client: TestClient) -> None:
    response = client.post("/reports/3/pipeline?email=asha@example.com")
    assert status_of(client, response)["result"] == "report-3.csv sent to asha@example.com"


def test_chord(client: TestClient) -> None:
    response = client.post("/reports/summary?course_ids=1&course_ids=2&course_ids=3")
    assert status_of(client, response)["result"] == {"courses": 3, "students": 4500}
    assert client.post("/reports/summary?course_ids=9").status_code == 404
    assert client.post("/reports/4/pipeline?email=asha@example.com").status_code == 422


def test_beat_schedule() -> None:
    schedule = celery_app.conf.beat_schedule
    assert schedule["heartbeat-every-5-seconds"]["schedule"] == 5.0
    assert schedule["daily-digest-7-30"]["schedule"] == crontab(hour=7, minute=30)
    assert schedule["weekly-report-monday"]["kwargs"] == {"weekly": True}


def test_workers_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeInspect:
        def __init__(self, active: dict | None) -> None:
            self._active = active

        def active(self) -> dict | None:
            return self._active

    busy = {"celery@pc": [{"name": "app.tasks.load_course"}]}
    monkeypatch.setattr(celery_app.control, "inspect", lambda timeout: FakeInspect(busy))
    response = client.get("/workers")
    assert response.json() == {"workers": ["celery@pc"],
                               "active": {"celery@pc": ["app.tasks.load_course"]}}
    monkeypatch.setattr(celery_app.control, "inspect", lambda timeout: FakeInspect(None))
    assert client.get("/workers").status_code == 503               # nobody answered
