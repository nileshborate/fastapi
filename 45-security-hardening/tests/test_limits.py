# Too big: bodies, strings, numbers, pages - and fields that must not come from outside
import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth


def test_a_huge_body_is_413(client: TestClient) -> None:
    headers = auth(client)
    response = client.post("/courses", json={"title": "x" * 1_000_000, "fee": 1},
                           headers=headers)
    assert response.status_code == 413
    assert response.json() == {"detail": "Request body too large"}


def test_a_chunked_body_without_content_length(client: TestClient) -> None:
    headers = auth(client) | {"Content-Type": "application/json"}

    def chunks():                                            # no Content-Length header!
        yield b'{"title": "'
        for _ in range(40):
            yield b"x" * 1024
        yield b'", "fee": 1}'
    response = client.post("/courses", content=chunks(), headers=headers)
    assert response.status_code == 413


@pytest.mark.parametrize(("body", "field"), [
    ({"title": "x" * 101, "fee": 1}, "title"),
    ({"title": "SQL Basics", "fee": 10**9}, "fee"),
    ({"title": "SQL Basics", "fee": -1}, "fee"),
    ({"title": "SQL Basics", "fee": 1, "owner_id": 7}, "owner_id"),
])
def test_bad_bodies_are_422(client: TestClient, body: dict, field: str) -> None:
    response = client.post("/courses", json=body, headers=auth(client))
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == field


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1", "q=" + "a" * 51])
def test_bad_queries_are_422(client: TestClient, query: str) -> None:
    assert client.get(f"/courses?{query}").status_code == 422


def test_paging_and_search(client: TestClient) -> None:
    headers = auth(client)
    for title in ("SQL Basics", "FastAPI Basics", "Docker 100% Practical"):
        client.post("/courses", json={"title": title, "fee": 1}, headers=headers)
    assert len(client.get("/courses?limit=2").json()) == 2
    assert [c["title"] for c in client.get("/courses?q=Basics").json()] == \
        ["SQL Basics", "FastAPI Basics"]
    assert len(client.get("/courses?q=%25").json()) == 1      # "%" is a letter, not a wildcard


def test_somebody_elses_course_is_404(client: TestClient) -> None:
    asha, ravi = auth(client), auth(client, "ravi@example.com")
    client.post("/courses", json={"title": "SQL Basics", "fee": 1}, headers=asha)
    response = client.patch("/courses/1", json={"fee": 0}, headers=ravi)
    assert response.status_code == 404                        # OWASP API1
