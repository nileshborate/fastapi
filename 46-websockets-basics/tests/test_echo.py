# The echo WebSocket - with the TestClient, no real server needed
from fastapi.testclient import TestClient


def test_echo_many_messages_one_connection(client: TestClient) -> None:
    with client.websocket_connect("/ws/echo") as websocket:
        websocket.send_text("hello")
        assert websocket.receive_text() == "echo: hello"
        websocket.send_text("how are you?")
        assert websocket.receive_text() == "echo: how are you?"


def test_a_normal_get_is_not_a_websocket(client: TestClient) -> None:
    assert client.get("/ws/echo").status_code == 404     # no HTTP route with this path
