# Liveness never checks dependencies · readiness does - critical vs non-critical
import pytest
from fastapi.testclient import TestClient

from app import health
from app.config import get_settings
from app.main import app
from tests.conftest import payments_down, payments_hangs


def test_ready_when_everything_is_up(client: TestClient) -> None:
    response = client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready" and body["version"] == "1.4.0"
    assert {c["status"] for c in body["checks"].values()} == {"up"}


def test_a_non_critical_dependency_only_degrades(client: TestClient,
                                                 monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(health.CHECKS, "payments", (payments_down, False))
    response = client.get("/health/ready")
    assert response.status_code == 200                   # still take traffic
    assert response.json()["status"] == "degraded"
    assert response.json()["checks"]["payments"]["error"] == "ConnectionError: payments is down"


def test_a_slow_check_times_out(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(health.CHECKS, "payments", (payments_hangs, False))
    monkeypatch.setattr(get_settings(), "check_timeout", 0.1)
    check = client.get("/health/ready").json()["checks"]["payments"]
    assert check == {"status": "down", "error": "timeout after 0.1 s", "ms": check["ms"]}
    assert check["ms"] < 500                             # it did NOT wait 5 seconds


def test_a_critical_dependency_means_not_ready(client: TestClient,
                                               monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "db_path", "/no/such/folder/x.db")
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert "unable to open database file" in response.json()["checks"]["database"]["error"]
    assert client.get("/health/live").status_code == 200     # alive - don't restart it


def test_draining_on_shutdown(client: TestClient) -> None:
    app.state.shutting_down = True
    try:
        response = client.get("/health/ready")
    finally:
        app.state.shutting_down = False
    assert (response.status_code, response.json()) == (503, {"status": "draining"})
