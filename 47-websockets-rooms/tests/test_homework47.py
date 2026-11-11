# Homework 47: the last 20 messages for new members + a teacher removes a student
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from tests.conftest import token


def test_a_new_member_gets_the_last_20_messages(client: TestClient) -> None:
    asha, ravi = token(client, "asha"), token(client, "ravi")
    with client.websocket_connect(f"/ws/rooms/python?token={asha}") as websocket:
        websocket.receive_json()                                  # asha joined
        for n in range(25):
            websocket.send_json({"text": f"message {n}"})
            websocket.receive_json()
    with client.websocket_connect(f"/ws/rooms/python?token={ravi}") as websocket:
        history = websocket.receive_json()
        assert history["type"] == "history"
        texts = [m["text"] for m in history["messages"]]
        assert texts == [f"message {n}" for n in range(5, 25)]     # only the last 20
        assert websocket.receive_json()["text"] == "ravi joined"


def test_an_empty_room_sends_no_history(client: TestClient) -> None:
    with client.websocket_connect(f"/ws/rooms/sql?token={token(client, 'meera')}") as ws:
        assert ws.receive_json()["type"] == "system"              # straight to "joined"


def test_a_teacher_removes_a_student(client: TestClient) -> None:
    ravi, asha = token(client, "ravi"), token(client, "asha")
    teacher = {"Authorization": f"Bearer {token(client, 'nilesh')}"}
    with client.websocket_connect(f"/ws/rooms/python?token={asha}") as asha_py:
        asha_py.receive_json()                                    # asha joined
        with client.websocket_connect(f"/ws/rooms/python?token={ravi}") as ravi_py:
            asha_py.receive_json()                                # ravi joined
            ravi_py.receive_json()
            response = client.delete("/rooms/python/members/ravi", headers=teacher)
            assert response.json() == {"room": "python", "removed": "ravi", "connections": 1}
            with pytest.raises(WebSocketDisconnect) as closed:
                ravi_py.receive_json()
            assert (closed.value.code, closed.value.reason) == (1008, "removed by teacher")
        # leaving the "with" completes the close - a real client does that by itself
        assert asha_py.receive_json()["text"] == "ravi left"
    assert client.delete("/rooms/python/members/ravi", headers=teacher).status_code == 404


def test_students_cannot_remove(client: TestClient) -> None:
    student = {"Authorization": f"Bearer {token(client, 'asha')}"}
    assert client.delete("/rooms/python/members/ravi", headers=student).status_code == 403
