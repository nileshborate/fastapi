# Refresh: rotation, reuse detection, and every kind of bad refresh token
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.database import SessionLocal
from app.models import RefreshToken, User
from app.security import _encode, create_refresh_token
from tests.conftest import bearer, login, refresh


def rows(client: TestClient) -> list[RefreshToken]:
    async def load() -> list[RefreshToken]:
        async with SessionLocal() as db:
            return list(await db.scalars(select(RefreshToken).order_by(RefreshToken.id)))
    return client.portal.call(load)


def test_refresh_gives_a_new_pair_and_kills_the_old_token(client: TestClient) -> None:
    first = login(client)
    response = refresh(client, first["refresh_token"])
    assert response.status_code == 200
    second = response.json()
    assert second["refresh_token"] != first["refresh_token"]
    assert client.get("/me", headers=bearer(second)).status_code == 200
    old, new = rows(client)
    assert old.revoked_at is not None and old.replaced_by == new.jti
    assert new.revoked_at is None


def test_reuse_logs_the_user_out_everywhere(client: TestClient) -> None:
    first = login(client)
    second = refresh(client, first["refresh_token"]).json()
    response = refresh(client, first["refresh_token"])          # the thief
    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token reuse detected"
    response = refresh(client, second["refresh_token"])         # Asha's good token: dead
    assert response.status_code == 401
    assert all(row.revoked_at is not None for row in rows(client))


def test_bad_refresh_tokens(client: TestClient) -> None:
    pair = login(client)
    expired, _, _ = create_refresh_token(1, days=-1)
    never_issued, _, _ = create_refresh_token(1)                # valid JWT - not in the table
    no_jti = _encode({"sub": "1", "type": "refresh", "exp": 9999999999})
    for token in ("abc.def.ghi", expired, never_issued, no_jti, pair["access_token"]):
        assert refresh(client, token).status_code == 401


def test_an_inactive_user_cannot_refresh(client: TestClient) -> None:
    pair = login(client)

    async def block() -> None:
        async with SessionLocal() as db:
            await db.execute(update(User).values(is_active=False))
            await db.commit()
    client.portal.call(block)
    assert refresh(client, pair["refresh_token"]).status_code == 401
