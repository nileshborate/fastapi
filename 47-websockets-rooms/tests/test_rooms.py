# Rooms: a message reaches its own room - and nobody else
from fastapi.testclient import TestClient

from app.rooms import rooms
from tests.conftest import token


def test_messages_stay_in_their_room(client: TestClient) -> None:
    asha, ravi, meera = (token(client, n) for n in ("asha", "ravi", "meera"))
    with client.websocket_connect(f"/ws/rooms/python?token={ravi}") as ravi_py, \
            client.websocket_connect(f"/ws/rooms/sql?token={meera}") as meera_sql, \
            client.websocket_connect(f"/ws/rooms/python?token={asha}") as asha_py:
        ravi_py.receive_json()                                    # ravi joined
        meera_sql.receive_json()                                  # meera joined (sql)
        joined = ravi_py.receive_json()
        assert joined["text"] == "asha joined" and joined["members"] == ["asha", "ravi"]
        asha_py.receive_json()
        asha_py.send_json({"text": "Python quiz tomorrow?"})
        chat = {"type": "chat", "room": "python", "from": "asha",
                "text": "Python quiz tomorrow?"}
        assert ravi_py.receive_json() == chat
        assert asha_py.receive_json() == chat
        with client.websocket_connect(f"/ws/rooms/sql?token={asha}") as asha_sql:
            asha_sql.receive_json()
            # the FIRST thing Meera gets is Asha joining sql - never the python chat
            assert meera_sql.receive_json()["text"] == "asha joined"
        assert meera_sql.receive_json()["text"] == "asha left"


def test_a_teacher_announces_to_one_room(client: TestClient) -> None:
    ravi, meera = token(client, "ravi"), token(client, "meera")
    teacher = {"Authorization": f"Bearer {token(client, 'nilesh')}"}
    with client.websocket_connect(f"/ws/rooms/python?token={ravi}") as ravi_py, \
            client.websocket_connect(f"/ws/rooms/sql?token={meera}") as meera_sql:
        ravi_py.receive_json()                                    # ravi joined
        meera_sql.receive_json()                                  # meera joined
        response = client.post("/rooms/python/announcements", json={"text": "Quiz at 5 pm"},
                               headers=teacher)
        assert response.status_code == 202
        assert response.json() == {"room": "python", "delivered_to": 1}
        assert ravi_py.receive_json() == {"type": "announcement", "room": "python",
                                          "from": "nilesh", "text": "Quiz at 5 pm"}
        client.post("/rooms/sql/announcements", json={"text": "SQL lab"}, headers=teacher)
        assert meera_sql.receive_json()["text"] == "SQL lab"     # not the python one


def test_students_cannot_announce(client: TestClient) -> None:
    student = {"Authorization": f"Bearer {token(client, 'asha')}"}
    response = client.post("/rooms/python/announcements", json={"text": "No class!"},
                           headers=student)
    assert response.status_code == 403


def test_a_bad_message_and_an_empty_room(client: TestClient) -> None:
    ravi = token(client, "ravi")
    with client.websocket_connect(f"/ws/rooms/python?token={ravi}") as websocket:
        websocket.receive_json()
        websocket.send_text("not json")
        assert websocket.receive_json()["type"] == "error"
    assert rooms.rooms == {}                                       # the empty room is gone
