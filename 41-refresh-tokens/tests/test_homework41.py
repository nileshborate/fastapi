# Homework 41: DELETE /me/sessions/{id} and PATCH /me/password
from fastapi.testclient import TestClient

from tests.conftest import bearer, login, refresh


def test_end_one_session(client: TestClient) -> None:
    phone, laptop = login(client), login(client)
    sessions = client.get("/me/sessions", headers=bearer(laptop)).json()
    assert [s["id"] for s in sessions] == [1, 2]
    assert client.delete("/me/sessions/1", headers=bearer(laptop)).status_code == 204
    assert refresh(client, phone["refresh_token"]).status_code == 401     # the phone is out
    assert refresh(client, laptop["refresh_token"]).status_code == 200    # the laptop isn't
    assert client.delete("/me/sessions/1", headers=bearer(laptop)).status_code == 404


def test_somebody_elses_session_is_404(client: TestClient) -> None:
    login(client)                                            # Asha: session 1
    ravi = login(client, "ravi@example.com")
    assert client.delete("/me/sessions/1", headers=bearer(ravi)).status_code == 404
    assert client.delete("/me/sessions/1").status_code == 401


def test_change_password_logs_out_everywhere(client: TestClient) -> None:
    phone, laptop = login(client), login(client)
    body = {"old_password": "blue-river-42", "new_password": "green-hill-77"}
    response = client.patch("/me/password", json=body, headers=bearer(laptop))
    assert response.status_code == 200
    fresh = response.json()                                  # this device stays in
    assert client.get("/me", headers=bearer(fresh)).status_code == 200
    assert client.get("/me", headers=bearer(phone)).status_code == 401    # old access tokens
    assert refresh(client, phone["refresh_token"]).status_code == 401     # old refresh tokens
    form = {"username": "asha@example.com", "password": "green-hill-77"}
    assert client.post("/token", data=form).status_code == 200


def test_change_password_needs_the_old_one(client: TestClient) -> None:
    pair = login(client)
    body = {"old_password": "wrong-password", "new_password": "green-hill-77"}
    response = client.patch("/me/password", json=body, headers=bearer(pair))
    assert response.status_code == 400 and response.json()["detail"] == "Old password is wrong"
    short = {"old_password": "blue-river-42", "new_password": "short"}
    assert client.patch("/me/password", json=short, headers=bearer(pair)).status_code == 422
