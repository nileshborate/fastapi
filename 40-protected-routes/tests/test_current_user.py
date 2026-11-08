# get_current_user: every way a token can be wrong
import jwt
import pytest
from fastapi.testclient import TestClient

from app.security import create_access_token
from tests.conftest import auth


def test_me_with_a_valid_token(client: TestClient) -> None:
    me = client.get("/me", headers=auth(client))
    assert me.status_code == 200 and me.json()["email"] == "asha@example.com"


def test_no_token(client: TestClient) -> None:
    response = client.get("/me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.parametrize("token", [
    "abc.def.ghi",                                                  # garbage
    create_access_token(1, minutes=-1),                             # expired
    jwt.encode({"sub": "1", "exp": 9999999999}, "y" * 40),          # another secret
    create_access_token(999),                                       # user doesn't exist
])
def test_bad_tokens_are_401(client: TestClient, token: str) -> None:
    auth(client)                                                    # user 1 exists
    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}
    assert response.headers["www-authenticate"] == "Bearer"


def test_inactive_user_is_403(client: TestClient) -> None:
    headers = auth(client)

    async def deactivate() -> None:
        from app.database import SessionLocal
        from app.models import User
        async with SessionLocal() as db:
            (await db.get(User, 1)).is_active = False
            await db.commit()
    client.portal.call(deactivate)
    response = client.get("/me", headers=headers)
    assert response.status_code == 403 and response.json() == {"detail": "Inactive user"}
