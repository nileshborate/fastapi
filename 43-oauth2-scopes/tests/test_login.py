# The client asks for scopes - the server grants at most what the role allows
import jwt
import pytest
from fastapi.testclient import TestClient

from tests.conftest import login


@pytest.mark.parametrize(("email", "asked", "granted"), [
    ("asha@example.com", None, "courses:delete courses:read courses:write me users:manage"),
    ("asha@example.com", "courses:read", "courses:read"),
    ("ravi@example.com", None, "courses:read courses:write me"),
    ("meera@example.com", None, "courses:read me"),
    ("meera@example.com", "me users:manage", "me"),           # asks too much -> less
    ("meera@example.com", "courses:write", ""),               # nothing allowed -> no scopes
])
def test_granted_scopes(client: TestClient, users, email: str, asked, granted: str) -> None:
    response = login(client, email, asked)
    assert response.status_code == 200 and response.json()["scope"] == granted
    claims = jwt.decode(response.json()["access_token"], options={"verify_signature": False})
    assert claims["scope"] == granted                         # ONE string, with spaces


def test_unknown_scope_and_wrong_password(client: TestClient, users) -> None:
    response = login(client, "meera@example.com", "me superpower")
    assert response.status_code == 400
    assert response.json()["detail"] == "Unknown scope: superpower"
    form = {"username": "meera@example.com", "password": "wrong-password"}
    assert client.post("/token", data=form).status_code == 401
