# Homework 46: private messages + no two students with the same name
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


def test_private_message_reaches_only_the_target(client: TestClient) -> None:
    with client.websocket_connect("/ws/class/Asha") as asha, \
            client.websocket_connect("/ws/class/Ravi") as ravi, \
            client.websocket_connect("/ws/class/Meera") as meera:
        for _ in range(3):
            asha.receive_json()                           # 3 x "joined"
        for _ in range(2):
            ravi.receive_json()
        meera.receive_json()
        asha.send_json({"to": "Ravi", "text": "Did you finish the homework?"})
        private = {"type": "private", "from": "Asha", "to": "Ravi",
                   "text": "Did you finish the homework?"}
        assert ravi.receive_json() == private
        assert asha.receive_json() == private             # the sender's copy
        asha.send_json({"text": "Hello everybody"})
        assert meera.receive_json()["text"] == "Hello everybody"   # Meera never got it


def test_private_message_to_somebody_offline(client: TestClient) -> None:
    with client.websocket_connect("/ws/class/Asha") as asha:
        asha.receive_json()
        asha.send_json({"to": "Ravi", "text": "hi"})
        assert asha.receive_json() == {"type": "error", "detail": "Ravi is not online"}


def test_the_same_name_twice_is_closed(client: TestClient) -> None:
    with client.websocket_connect("/ws/class/Asha") as asha:
        asha.receive_json()
        with pytest.raises(WebSocketDisconnect) as closed:
            with client.websocket_connect("/ws/class/Asha") as second:
                second.receive_json()
        assert (closed.value.code, closed.value.reason) == (1008, "name taken")
        assert client.get("/online").json() == {"online": ["Asha"]}   # the first one stays
