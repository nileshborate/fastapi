# Checking a password: one message for every failure, old hashes get upgraded
import httpx
import pytest
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher
from sqlalchemy import select

from app.database import SessionLocal
from app.models import User

pytestmark = pytest.mark.anyio

ASHA = {"email": "asha@example.com", "full_name": "Asha Patil", "password": "blue-river-42"}


async def check(api: httpx.AsyncClient, email: str, password: str) -> httpx.Response:
    return await api.post("/auth/check", json={"email": email, "password": password})


async def test_right_password(api: httpx.AsyncClient) -> None:
    await api.post("/users", json=ASHA)
    response = await check(api, "ASHA@example.com", "blue-river-42")
    assert response.status_code == 200 and response.json()["id"] == 1


async def test_wrong_password_and_unknown_email_look_the_same(api: httpx.AsyncClient) -> None:
    await api.post("/users", json=ASHA)
    wrong = await check(api, "asha@example.com", "blue-river-43")
    unknown = await check(api, "nobody@example.com", "blue-river-42")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json() == {"detail": "Wrong email or password"}
    assert wrong.headers["www-authenticate"] == "Bearer"


async def test_old_bcrypt_hash_is_upgraded(api: httpx.AsyncClient) -> None:
    old_hash = PasswordHash((BcryptHasher(),)).hash("blue-river-42")    # an OLD system
    async with SessionLocal() as db:
        db.add(User(email="old@example.com", full_name="Old User", password_hash=old_hash))
        await db.commit()
    assert (await check(api, "old@example.com", "blue-river-42")).status_code == 200
    async with SessionLocal() as db:
        user = await db.scalar(select(User))
    assert user.password_hash.startswith("$argon2id$")                 # upgraded at login


async def test_inactive_user(api: httpx.AsyncClient) -> None:
    await api.post("/users", json=ASHA)
    async with SessionLocal() as db:
        user = await db.scalar(select(User))
        user.is_active = False
        await db.commit()
    assert (await check(api, "asha@example.com", "blue-river-42")).status_code == 401
