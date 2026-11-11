# Auth over WebSockets: the token comes as ?token=... - checked before accept
import time
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.security import create_access_token
from tests.conftest import token


def refused(client: TestClient, url: str) -> tuple[int, str]:
    with pytest.raises(WebSocketDisconnect) as closed:
        with client.websocket_connect(url) as websocket:
            websocket.receive_json()
    return closed.value.code, closed.value.reason


@pytest.mark.parametrize("query", ["", "?token=garbage", "?token="])
def test_no_or_bad_token_is_refused(client: TestClient, query: str) -> None:
    assert refused(client, f"/ws/rooms/python{query}") == (1008, "invalid or missing token")


def test_an_expired_token_is_refused(client: TestClient) -> None:
    old = create_access_token("asha", timedelta(minutes=-1))
    assert refused(client, f"/ws/rooms/python?token={old}")[0] == 1008


def test_not_enrolled_is_refused(client: TestClient) -> None:
    ravi = token(client, "ravi")                           # Ravi: python only
    assert refused(client, f"/ws/rooms/sql?token={ravi}") == (1008, "not enrolled in this room")


def test_the_connection_closes_when_the_token_expires(client: TestClient) -> None:
    short = create_access_token("asha", timedelta(seconds=2))   # exp: whole seconds
    start = time.monotonic()
    with client.websocket_connect(f"/ws/rooms/python?token={short}") as websocket:
        assert websocket.receive_json()["text"] == "asha joined"
        with pytest.raises(WebSocketDisconnect) as closed:
            websocket.receive_json()                       # nothing to read - until exp
    assert (closed.value.code, closed.value.reason) == (1008, "token expired")
    assert 0.9 < time.monotonic() - start < 3                # closed by the SERVER


def test_http_routes_still_use_the_header(client: TestClient) -> None:
    assert client.get("/rooms/python/members").status_code == 401
    headers = {"Authorization": f"Bearer {token(client, 'ravi')}"}
    assert client.get("/rooms/python/members", headers=headers).json() == \
        {"room": "python", "members": []}
    assert client.get("/rooms/sql/members", headers=headers).status_code == 404
