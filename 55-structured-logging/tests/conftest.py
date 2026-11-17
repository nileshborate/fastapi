import io
import json
import logging
from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient

from app import services
from app.logging_setup import JsonFormatter, RequestIdFilter
from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    services.ENROLLED.clear()
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def logs() -> Iterator[Callable[[], list[dict]]]:
    """every JSON line our app writes during the test, already parsed"""
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RequestIdFilter())
    root = logging.getLogger()
    root.addHandler(handler)
    old_level = root.level
    root.setLevel(logging.DEBUG)
    yield lambda: [json.loads(line) for line in stream.getvalue().splitlines()
                   if json.loads(line)["logger"].startswith("app")]
    root.removeHandler(handler)
    root.setLevel(old_level)
