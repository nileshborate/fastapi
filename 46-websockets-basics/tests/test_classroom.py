# The live classroom: join, chat, errors, leave, announcements over HTTP
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


def test_join_and_chat_reaches_everybody(client: TestClient) -> None:
    with client.websocket_connect("/ws/class/Asha") as asha:
        assert asha.receive_json() == {"type": "system", "text": "Asha joined",
                                       "online": ["Asha"]}
        with client.websocket_connect("/ws/class/Ravi") as ravi:
            joined = {"type": "system", "text": "Ravi joined", "online": ["Asha", "Ravi"]}
            assert asha.receive_json() == joined          # Asha hears about Ravi
            assert ravi.receive_json() == joined
            ravi.send_json({"text": "Hello class!"})
            chat = {"type": "chat", "from": "Ravi", "text": "Hello class!"}
            assert asha.receive_json() == chat            # pushed - Asha never asked
            assert ravi.receive_json() == chat
        left = asha.receive_json()                        # Ravi's "with" block closed
        assert left == {"type": "system", "text": "Ravi left", "online": ["Asha"]}


def test_a_bad_message_goes_back_only_to_the_sender(client: TestClient) -> None:
    with client.websocket_connect("/ws/class/Asha") as asha:
        asha.receive_json()
        for bad in ('{"text": ""}', "not json", '{"text": "hi", "admin": true}',
                    '{"text": "' + "x" * 501 + '"}'):
            asha.send_text(bad)
            assert asha.receive_json()["type"] == "error"
        asha.send_json({"text": "still here"})
        assert asha.receive_json()["text"] == "still here"   # the connection survived


@pytest.mark.parametrize("name", ["A", "Asha1", "x" * 21])
def test_a_bad_name_is_closed_with_1008(client: TestClient, name: str) -> None:
    with pytest.raises(WebSocketDisconnect) as closed:
        with client.websocket_connect(f"/ws/class/{name}") as websocket:
            websocket.receive_json()
    assert closed.value.code == 1008                       # policy violation


def test_announcement_over_http_reaches_every_socket(client: TestClient) -> None:
    with client.websocket_connect("/ws/class/Asha") as asha, \
            client.websocket_connect("/ws/class/Ravi") as ravi:
        for _ in range(2):
            asha.receive_json()                           # "Asha joined", "Ravi joined"
        ravi.receive_json()                               # "Ravi joined"
        assert client.get("/online").json() == {"online": ["Asha", "Ravi"]}
        response = client.post("/announcements", json={"text": "Quiz at 5 pm"})
        assert response.status_code == 202
        assert response.json() == {"delivered_to": 2}
        message = {"type": "announcement", "text": "Quiz at 5 pm"}
        assert asha.receive_json() == message
        assert ravi.receive_json() == message
    assert client.get("/online").json() == {"online": []}
    assert client.post("/announcements", json={"text": ""}).status_code == 422
