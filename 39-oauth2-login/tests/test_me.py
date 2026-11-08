# GET /users/me - OAuth2PasswordBearer reads the token
from fastapi.testclient import TestClient

from tests.conftest import get_token


def test_me_with_a_token(client: TestClient) -> None:
    headers = {"Authorization": f"Bearer {get_token(client)}"}
    me = client.get("/users/me", headers=headers).json()
    assert me["email"] == "asha@example.com" and "password_hash" not in me


def test_no_token_is_401(client: TestClient) -> None:
    response = client.get("/users/me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}   # from OAuth2PasswordBearer
    assert response.headers["www-authenticate"] == "Bearer"


def test_bad_token_is_401(client: TestClient) -> None:
    response = client.get("/users/me", headers={"Authorization": "Bearer abc.def.ghi"})
    assert response.json() == {"detail": "Could not validate credentials"}


def test_openapi_has_the_security_scheme(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()
    scheme = spec["components"]["securitySchemes"]["OAuth2PasswordBearer"]
    assert scheme["flows"]["password"]["tokenUrl"] == "token"
    assert spec["paths"]["/users/me"]["get"]["security"] == [{"OAuth2PasswordBearer": []}]
