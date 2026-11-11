from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:                  # runs the lifespan: the report file
        yield test_client


def sse_events(text: str) -> list[dict[str, str]]:
    """parse the text/event-stream format: blocks separated by a blank line"""
    events = []
    for block in text.strip().split("\n\n"):
        fields = dict(line.split(": ", 1) for line in block.splitlines() if ": " in line)
        events.append(fields)
    return events
