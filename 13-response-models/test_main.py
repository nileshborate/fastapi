# Run:  pytest -v
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)
ASHA: dict[str, Any] = {"name": "Asha Patil", "email": "asha@example.com", "password": "secret123"}


@pytest.fixture(autouse=True)
def reset_data() -> Iterator[None]:
    main.USERS.clear()
    yield


def test_create_returns_201_without_password() -> None:
    response = client.post("/users", json=ASHA)
    assert response.status_code == 201
    assert response.json() == {"id": 1, "name": "Asha Patil", "email": "asha@example.com", "bio": None}


def test_password_is_stored_hashed() -> None:
    client.post("/users", json=ASHA)
    assert main.USERS[1].hashed_password != "secret123"


def test_list_hides_passwords() -> None:
    client.post("/users", json=ASHA)
    body = client.get("/users").json()
    assert "hashed_password" not in body[0] and "password" not in body[0]


def test_get_user_excludes_none() -> None:
    client.post("/users", json=ASHA)
    assert client.get("/users/1").json() == {"id": 1, "name": "Asha Patil", "email": "asha@example.com"}


def test_get_missing_user_404() -> None:
    assert client.get("/users/99").status_code == 404


def test_delete_returns_204_with_no_body() -> None:
    client.post("/users", json=ASHA)
    response = client.delete("/users/1")
    assert response.status_code == 204
    assert response.content == b""
    assert client.delete("/users/1").status_code == 404


def test_put_creates_201_then_updates_200() -> None:
    assert client.put("/users/7", json=ASHA).status_code == 201
    assert client.put("/users/7", json={**ASHA, "name": "Asha P"}).status_code == 200


def test_openapi_shows_status_codes() -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert "201" in paths["/users"]["post"]["responses"]
    assert "204" in paths["/users/{user_id}"]["delete"]["responses"]
    assert "404" in paths["/users/{user_id}"]["get"]["responses"]
