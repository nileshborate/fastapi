# Homework 43: the scope "courses:delete" and GET /me/token
from fastapi.testclient import TestClient

from tests.conftest import bearer, login


def test_only_admins_can_get_courses_delete(client: TestClient, users) -> None:
    assert "courses:delete" in login(client, "asha@example.com").json()["scope"].split()
    assert "courses:delete" not in login(client, "ravi@example.com").json()["scope"].split()
    asked = login(client, "ravi@example.com", "courses:delete").json()
    assert asked["scope"] == ""                                     # asked - not granted


def test_delete_a_course(client: TestClient, users) -> None:
    ravi = bearer(login(client, "ravi@example.com"))
    client.post("/courses", json={"title": "SQL Basics", "fee": 199}, headers=ravi)
    asha_read = bearer(login(client, "asha@example.com", "courses:read"))
    asha_all = bearer(login(client, "asha@example.com"))
    assert client.delete("/courses/1", headers=ravi).status_code == 403          # teacher
    assert client.delete("/courses/1", headers=asha_read).status_code == 403     # token
    assert client.delete("/courses/1", headers=asha_all).status_code == 204
    assert client.delete("/courses/1", headers=asha_all).status_code == 404


def test_my_token(client: TestClient, users) -> None:
    pair = login(client, "ravi@example.com", "me courses:read")
    body = client.get("/me/token", headers=bearer(pair)).json()
    assert body["user_id"] == 2 and body["scopes"] == ["courses:read", "me"]
    assert 890 <= body["expires_in"] <= 900                         # 15 minutes
    no_me = bearer(login(client, "ravi@example.com", "courses:read"))
    assert client.get("/me/token", headers=no_me).status_code == 403   # needs "me"
    assert client.get("/me/token").status_code == 401
