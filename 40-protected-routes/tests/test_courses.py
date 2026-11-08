# Public, protected, and owner-only routes
from fastapi.testclient import TestClient

from tests.conftest import auth

COURSE = {"title": "FastAPI Basics", "fee": 299}


def test_listing_is_public(client: TestClient) -> None:
    assert client.get("/courses").json() == []


def test_creating_needs_a_login(client: TestClient) -> None:
    assert client.post("/courses", json=COURSE).status_code == 401
    created = client.post("/courses", json=COURSE, headers=auth(client))
    assert created.status_code == 201
    assert created.json()["owner_id"] == 1 and created.json()["is_mine"] is True


def test_owner_id_comes_from_the_token_not_the_body(client: TestClient) -> None:
    response = client.post("/courses", json={**COURSE, "owner_id": 2}, headers=auth(client))
    assert response.status_code == 422                     # extra="forbid": not your choice


def test_is_mine_for_a_logged_in_user(client: TestClient) -> None:
    asha, ravi = auth(client), auth(client, "ravi@example.com")
    client.post("/courses", json=COURSE, headers=asha)
    assert client.get("/courses").json()[0]["is_mine"] is False               # a guest
    assert client.get("/courses", headers=asha).json()[0]["is_mine"] is True
    assert client.get("/courses", headers=ravi).json()[0]["is_mine"] is False


def test_only_the_owner_can_change_or_delete(client: TestClient) -> None:
    asha, ravi = auth(client), auth(client, "ravi@example.com")
    client.post("/courses", json=COURSE, headers=asha)
    assert client.patch("/courses/1", json={"fee": 1}).status_code == 401      # who are you?
    response = client.patch("/courses/1", json={"fee": 1}, headers=ravi)
    assert response.status_code == 403                                          # not yours
    assert response.json() == {"detail": "Only the owner can change this course"}
    assert client.delete("/courses/1", headers=ravi).status_code == 403
    assert client.patch("/courses/1", json={"fee": 349}, headers=asha).json()["fee"] == 349
    assert client.delete("/courses/1", headers=asha).status_code == 204
    assert client.delete("/courses/1", headers=asha).status_code == 404


def test_my_courses(client: TestClient) -> None:
    asha, ravi = auth(client), auth(client, "ravi@example.com")
    client.post("/courses", json=COURSE, headers=asha)
    client.post("/courses", json={"title": "Docker Deep Dive", "fee": 499}, headers=ravi)
    assert [c["title"] for c in client.get("/me/courses", headers=asha).json()] == [
        "FastAPI Basics"]
    assert client.get("/me/courses").status_code == 401        # the whole router is protected
