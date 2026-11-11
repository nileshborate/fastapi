# Every endpoint checks its scope - in the token AND in the user's role
import pytest
from fastapi.testclient import TestClient

from demos.stacking import app as stacking_app
from tests.conftest import bearer, login

TOKENS = [("meera@example.com", None), ("ravi@example.com", None),
          ("ravi@example.com", "courses:read"), ("asha@example.com", None),
          ("asha@example.com", "courses:read")]
MATRIX = [
    ("GET", "/me", (200, 200, 403, 200, 403)),
    ("GET", "/courses", (200, 200, 200, 200, 200)),
    ("POST", "/courses", (403, 201, 403, 201, 403)),
    ("GET", "/admin/users", (403, 403, 403, 200, 403)),
]


@pytest.mark.parametrize(("method", "url", "expected"), MATRIX)
def test_matrix(client: TestClient, users, method: str, url: str, expected) -> None:
    body = {"title": "SQL Basics", "fee": 199} if method == "POST" else None
    headers = [bearer(login(client, email, scope)) for email, scope in TOKENS]
    codes = tuple(client.request(method, url, json=body, headers=h).status_code
                  for h in headers)
    assert codes == expected


def test_the_answer_says_which_scope(client: TestClient, users) -> None:
    read_only = bearer(login(client, "asha@example.com", "courses:read"))
    course = {"title": "SQL Basics", "fee": 199}
    response = client.post("/courses", json=course, headers=read_only)
    assert response.status_code == 403
    assert response.json()["detail"] == "The token doesn't have the scope: courses:write"
    header = response.headers["www-authenticate"]
    assert header == 'Bearer error="insufficient_scope", scope="courses:write"'
    response = client.post("/courses", json={}, headers={"Authorization": "Bearer abc"})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == 'Bearer scope="courses:write"'


def test_the_role_still_counts(client: TestClient, users) -> None:
    ravi = bearer(login(client, "ravi@example.com"))          # has courses:write
    asha = bearer(login(client, "asha@example.com"))
    client.patch("/admin/users/2/role", json={"role": "student"}, headers=asha)
    response = client.post("/courses", json={"title": "Docker", "fee": 399}, headers=ravi)
    assert response.status_code == 403
    assert response.json()["detail"] == "Your role doesn't allow the scope: courses:write"


def test_security_scopes_stack_up() -> None:
    with TestClient(stacking_app) as c:
        assert c.get("/stacked").json() == ["courses:write", "courses:read"]
        assert c.get("/twice").json() == [["me"], ["courses:read"]]


def test_openapi_knows_the_scopes(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    flow = schema["components"]["securitySchemes"]["OAuth2PasswordBearer"]["flows"]["password"]
    assert set(flow["scopes"]) == {"me", "courses:read", "courses:write", "courses:delete",
                                   "users:manage"}
    post = schema["paths"]["/courses"]["post"]["security"]
    assert post == [{"OAuth2PasswordBearer": ["courses:write"]}]
