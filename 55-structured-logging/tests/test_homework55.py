# Homework 55: a slow-request warning, and client_ip + user_agent on request.done
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings

Logs = Callable[[], list[dict]]


@pytest.fixture
def slow_ms_100(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(get_settings(), "slow_ms", 100)     # a report takes ~300 ms


def test_a_slow_request_is_a_warning(client: TestClient, logs: Logs, slow_ms_100) -> None:
    client.get("/reports/1")
    slow = [e for e in logs() if e["event"] == "request.slow"]
    assert len(slow) == 1
    assert slow[0]["level"] == "WARNING" and slow[0]["path"] == "/reports/1"
    assert slow[0]["duration_ms"] > 100


def test_a_fast_request_is_not(client: TestClient, logs: Logs, slow_ms_100) -> None:
    client.post("/enrollments", json={"email": "asha@example.com", "course_id": 2,
                                      "card_number": "4111111111111111"})
    assert "request.slow" not in [e["event"] for e in logs()]


def test_client_ip_and_user_agent(client: TestClient, logs: Logs) -> None:
    client.get("/reports/1", headers={"User-Agent": "course-app/3.1"})
    done = logs()[-1]
    assert done["event"] == "request.done"
    assert done["client_ip"] == "testclient"                # TestClient's fake address
    assert done["user_agent"] == "course-app/3.1"
