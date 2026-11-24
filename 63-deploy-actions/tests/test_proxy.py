# Behind Nginx: uvicorn's ProxyHeadersMiddleware turns X-Forwarded-* into the REAL client
# and scheme - only for requests from an address it trusts (FORWARDED_ALLOW_IPS: 127.0.0.1)
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app import main

FROM_NGINX = {"X-Forwarded-Proto": "https", "X-Forwarded-For": "203.0.113.7"}


def behind_proxy(trusted: str) -> Iterator[TestClient]:
    with TestClient(ProxyHeadersMiddleware(main.app, trusted_hosts=trusted)) as test_client:
        with main.db.connection() as conn:
            conn.execute("TRUNCATE courses RESTART IDENTITY")
        yield test_client


@pytest.fixture
def trusting() -> Iterator[TestClient]:
    yield from behind_proxy("*")                 # FORWARDED_ALLOW_IPS="*" in compose.yaml


@pytest.fixture
def default() -> Iterator[TestClient]:
    yield from behind_proxy("127.0.0.1")         # uvicorn's default - nginx is NOT 127.0.0.1


def test_trusted_headers_give_the_real_client(trusting: TestClient) -> None:
    me = trusting.get("/whoami", headers=FROM_NGINX).json()
    assert me["client"] == "203.0.113.7" and me["scheme"] == "https"
    assert me["url"] == "https://testserver/whoami"


def test_untrusted_headers_are_ignored(default: TestClient) -> None:
    me = default.get("/whoami", headers=FROM_NGINX).json()
    assert me["client"] == "testclient" and me["scheme"] == "http"
    assert me["x_forwarded_for"] == "203.0.113.7"          # the header is there - just not used


def test_links_use_https_behind_the_proxy(trusting: TestClient, default: TestClient) -> None:
    body = {"title": "Nginx + HTTPS"}
    created = trusting.post("/courses", json=body, headers=FROM_NGINX)
    assert created.headers["location"] == "https://testserver/courses/1"
    wrong = default.post("/courses", json=body, headers=FROM_NGINX)
    assert wrong.headers["location"].startswith("http://")  # mixed content in a browser


def test_the_trailing_slash_redirect_keeps_https(trusting: TestClient) -> None:
    response = trusting.get("/courses/", headers=FROM_NGINX, follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "https://testserver/courses"
