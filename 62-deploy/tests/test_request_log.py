# Homework 61.2: nginx's $request_id arrives as X-Request-ID - and is in the api's log
import json
import logging
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.request_log import log


class Lines(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.lines: list[dict] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(json.loads(record.getMessage()))


@pytest.fixture
def logged() -> Iterator[list[dict]]:
    handler = Lines()
    log.addHandler(handler)
    yield handler.lines
    log.removeHandler(handler)


def test_the_request_id_from_nginx_is_logged(client: TestClient, logged: list[dict]) -> None:
    rid = "3f2a9c0e7b1d4e8f9a6b5c4d3e2f1a0b"               # 32 hex characters, like nginx
    client.get("/courses", headers={"X-Request-ID": rid})
    assert logged[-1]["request_id"] == rid
    assert logged[-1]["path"] == "/courses" and logged[-1]["status"] == 200


def test_without_nginx_the_api_makes_its_own(client: TestClient, logged: list[dict]) -> None:
    client.post("/courses", json={"title": "Static files"})
    line = logged[-1]
    assert len(line["request_id"]) == 32 and line["method"] == "POST"
    assert line["status"] == 201 and line["duration_ms"] >= 0
