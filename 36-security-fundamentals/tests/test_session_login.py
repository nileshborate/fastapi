# Sessions: the server remembers - logout works at once
from fastapi.testclient import TestClient

from app.sessions import SESSIONS
from tests.conftest import STUDENT


def login(client: TestClient, username: str, password: str):  # noqa: ANN201
    return client.post("/session/login", json={"username": username, "password": password})


def test_login_sets_a_cookie(client: TestClient) -> None:
    response = login(client, *STUDENT)
    assert response.json() == {"username": "asha", "role": "student"}
    cookie = response.headers["set-cookie"]
    assert "session_id=" in cookie and "HttpOnly" in cookie and "SameSite=lax" in cookie
    assert len(SESSIONS) == 1                                   # the server remembers
    assert client.get("/session/me").json()["username"] == "asha"   # cookie sent back


def test_wrong_password_and_unknown_user_look_the_same(client: TestClient) -> None:
    wrong = login(client, "asha", "nope")
    unknown = login(client, "nobody", "nope")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json() == {"detail": "Wrong username or password"}


def test_logout_works_at_once(client: TestClient) -> None:
    login(client, *STUDENT)
    assert client.post("/session/logout").status_code == 204
    assert SESSIONS == {}
    assert client.get("/session/me").status_code == 401
