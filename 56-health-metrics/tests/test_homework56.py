# Homework 56: a critical Redis check, and app_info{version} = 1
from collections.abc import Callable

import pytest
import redis
from fastapi.testclient import TestClient

from app import health


def test_redis_is_checked(client: TestClient) -> None:
    body = client.get("/health/ready").json()
    assert body["status"] == "ready" and body["checks"]["redis"]["status"] == "up"


def test_redis_down_means_not_ready(client: TestClient,
                                    monkeypatch: pytest.MonkeyPatch) -> None:
    async def refused() -> None:
        raise redis.ConnectionError("Connection refused")
    monkeypatch.setitem(health.CHECKS, "redis", (refused, True))     # critical
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["checks"]["redis"]["error"] == "ConnectionError: Connection refused"


def test_app_info(client: TestClient, metric: Callable[..., float]) -> None:
    assert metric("app_info", version="1.4.0") == 1
    assert 'app_info{version="1.4.0"} 1.0' in client.get("/metrics").text
