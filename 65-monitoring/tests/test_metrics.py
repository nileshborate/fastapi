# Video 65: what Prometheus reads - and what it must NOT see (one series per id, a 500 hidden)
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from app import main

ROOT = Path(__file__).resolve().parents[1]


def series(client: TestClient, name: str) -> list[str]:
    return [line for line in client.get("/metrics").text.splitlines() if line.startswith(name)]


def test_metrics_say_which_version_runs(client: TestClient) -> None:
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    version = main.settings.version          # not "1.14.0": a release must not break it
    assert f'coursehub_info{{commit="dev",version="{version}"}} 1.0' in response.text


def test_one_series_per_route_not_per_id(client: TestClient) -> None:
    for course_id in (1, 2, 3, 999):
        client.get(f"/courses/{course_id}")
    lines = series(client, "http_requests_total")
    routes = {line.split('route="')[1].split('"')[0] for line in lines}
    assert "/courses/{course_id}" in routes
    assert not any(route.startswith("/courses/") and "{" not in route for route in routes)


def test_a_scanner_cannot_create_new_series(client: TestClient) -> None:
    before = len(series(client, "http_requests_total"))
    for path in ("/wp-login.php", "/.env", "/admin", "/x/y/z"):
        assert client.get(path).status_code == 404
    lines = series(client, "http_requests_total")
    assert len(lines) <= before + 1                     # at most ONE new series: "unmatched"
    assert any('route="unmatched"' in line and 'status="404"' in line for line in lines)


def test_an_exception_is_counted_as_a_500(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken() -> list:
        raise RuntimeError("the database is gone")

    monkeypatch.setattr(main.db, "list_courses", broken)
    with TestClient(main.app, raise_server_exceptions=False) as client:
        assert client.get("/courses").status_code == 500
        assert any('route="/courses"' in line and 'status="500"' in line
                   for line in series(client, "http_requests_total"))


def test_metrics_are_not_public() -> None:
    conf = (ROOT / "nginx" / "default.conf").read_text()
    assert "location = /metrics {\n        return 404;" in conf
    services = yaml.safe_load((ROOT / "compose.yaml").read_text())["services"]
    for name in ("prometheus", "alertmanager"):           # 127.0.0.1: an SSH tunnel only
        assert all(port.startswith("127.0.0.1:") for port in services[name]["ports"])


def test_api_down_survives_a_container_that_is_gone() -> None:
    groups = yaml.safe_load((ROOT / "monitoring" / "rules.yml").read_text())["groups"]
    api_down = next(rule for rule in groups[0]["rules"] if rule["alert"] == "ApiDown")
    assert api_down["expr"] == 'absent(up{job="coursehub-api"} == 1)'   # not "up == 0"
