# Registration: 201 without any password in the answer, unique email, password rules
import httpx
import pytest
from sqlalchemy import select

from app.database import SessionLocal
from app.errors import ConflictError
from app.models import User
from app.uow import UnitOfWork

pytestmark = pytest.mark.anyio

ASHA = {"email": "Asha@Example.com", "full_name": "Asha Patil", "password": "blue-river-42"}


async def test_register(api: httpx.AsyncClient) -> None:
    response = await api.post("/users", json=ASHA)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "asha@example.com"                  # lower case
    assert body["is_active"] is True and "created_at" in body
    assert "password" not in body and "password_hash" not in body
    async with SessionLocal() as db:
        user = await db.scalar(select(User))
    assert user.password_hash.startswith("$argon2id$")          # only the hash is stored
    assert "blue-river-42" not in user.password_hash


async def test_email_is_unique_in_any_case(api: httpx.AsyncClient) -> None:
    await api.post("/users", json=ASHA)
    again = await api.post("/users", json={**ASHA, "email": "ASHA@example.COM"})
    assert again.status_code == 409
    assert again.json() == {"detail": "Email already registered"}


@pytest.mark.parametrize(("change", "message"), [
    ({"email": "not-an-email"}, "valid email"),
    ({"password": "short"}, "at least 8 characters"),
    ({"password": "Password123"}, "too common"),
    ({"password": "asha-1234567"}, "must not contain your email name"),
    ({"is_admin": True}, "Extra inputs"),
])
async def test_rules(api: httpx.AsyncClient, change: dict, message: str) -> None:
    response = await api.post("/users", json={**ASHA, **change})
    assert response.status_code == 422
    assert message in str(response.json())


async def test_get_user(api: httpx.AsyncClient) -> None:
    await api.post("/users", json=ASHA)
    assert (await api.get("/users/1")).json()["full_name"] == "Asha Patil"
    assert (await api.get("/users/9")).status_code == 404


async def test_unique_index_is_the_safety_net(api: httpx.AsyncClient) -> None:
    async with UnitOfWork() as uow:                 # two sign-ups at the same moment:
        for _ in range(2):                          # both passed the "exists?" check
            uow.users.add(User(email="asha@example.com", full_name="Asha", password_hash="x"))
        with pytest.raises(ConflictError, match="Email already registered"):
            await uow.commit()
