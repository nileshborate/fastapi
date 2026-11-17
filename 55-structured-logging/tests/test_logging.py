# Structured logs: valid JSON, one request id per request, fields, errors, secrets
import asyncio
import json
import logging
from collections.abc import Callable

import httpx
from fastapi.testclient import TestClient

from app.logging_setup import JsonFormatter, RequestIdFilter, request_id_var
from app.main import app

Logs = Callable[[], list[dict]]
CARD = {"email": "asha@example.com", "course_id": 2, "card_number": "4111111111111111"}


def _format(record: logging.LogRecord) -> dict:
    RequestIdFilter().filter(record)
    return json.loads(JsonFormatter().format(record))


def test_a_line_is_json_with_fields() -> None:
    record = logging.makeLogRecord({"name": "app.x", "levelname": "INFO", "msg": "order.paid",
                                    "order_id": 7})
    entry = _format(record)
    assert entry["event"] == "order.paid" and entry["order_id"] == 7
    assert entry["request_id"] == "-"                      # outside a request
    assert entry["service"] == "course-hub" and entry["ts"].endswith("+00:00")


def test_the_request_id_is_in_the_header_and_every_line(client: TestClient, logs: Logs) -> None:
    response = client.get("/reports/2")
    rid = response.headers["x-request-id"]
    assert len(rid) == 12
    lines = logs()
    assert [e["event"] for e in lines] == ["report.started", "report.step", "report.step",
                                           "report.step", "report.finished", "request.done"]
    assert {e["request_id"] for e in lines} == {rid}


def test_an_incoming_request_id_is_reused(client: TestClient, logs: Logs) -> None:
    response = client.get("/reports/1", headers={"X-Request-ID": "support-42"})
    assert response.headers["x-request-id"] == "support-42"
    assert {e["request_id"] for e in logs()} == {"support-42"}


def test_the_access_line(client: TestClient, logs: Logs) -> None:
    client.post("/enrollments", json=CARD | {"course_id": 9})
    done = logs()[-1]
    assert (done["event"], done["method"], done["path"], done["status"]) == (
        "request.done", "POST", "/enrollments", 404)
    assert done["duration_ms"] >= 0
    assert logs()[0]["level"] == "WARNING"                 # enrollment.unknown_course


def test_events_with_fields_and_a_hidden_card(client: TestClient, logs: Logs) -> None:
    assert client.post("/enrollments", json=CARD).status_code == 201
    assert client.post("/enrollments", json=CARD).status_code == 200      # a duplicate
    events = {e["event"]: e for e in logs()}
    assert events["enrollment.created"]["course"] == "SQL Joins"
    assert events["payment.charging"]["card_number"] == "***"
    assert "4111111111111111" not in json.dumps(logs())
    assert "enrollment.duplicate" in events


def test_an_error_is_logged_with_its_traceback(client: TestClient, logs: Logs) -> None:
    response = client.get("/boom", headers={"X-Request-ID": "support-42"})
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error", "request_id": "support-42"}
    failed = next(e for e in logs() if e["event"] == "request.failed")
    assert failed["level"] == "ERROR" and failed["exc_type"] == "ZeroDivisionError"
    assert "100 / students" in failed["traceback"]
    assert logs()[-1]["status"] == 500


def test_concurrent_requests_never_mix_ids(logs: Logs) -> None:
    async def three() -> list[httpx.Response]:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            return await asyncio.gather(*(c.get(f"/reports/{n}") for n in (1, 2, 3)))

    responses = asyncio.run(three())
    for r in responses:
        mine = [e for e in logs() if e["request_id"] == r.headers["x-request-id"]]
        assert len(mine) == 6
        assert {e.get("course_id") for e in mine[:-1]} == {r.json()["course_id"]}
    assert request_id_var.get() == "-"                    # reset after each request
