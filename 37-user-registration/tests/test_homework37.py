# Homework answer (Video 37): change the password, find a user by email
import httpx
import pytest
from sqlalchemy import select

from app.database import SessionLocal
from app.models import User

pytestmark = pytest.mark.anyio

ASHA = {"email": "asha@example.com", "full_name": "Asha Patil", "password": "blue-river-42"}


async def stored_hash() -> str:
    async with SessionLocal() as db:
        return (await db.scalar(select(User))).password_hash


async def test_change_password(api: httpx.AsyncClient) -> None:
    await api.post("/users", json=ASHA)
    before = await stored_hash()
    url = "/users/1/password"
    wrong = {"old_password": "nope", "new_password": "green-hill-77"}
    assert (await api.patch(url, json=wrong)).status_code == 401
    common = {"old_password": "blue-river-42", "new_password": "password123"}
    response = await api.patch(url, json=common)
    assert response.json() == {"detail": "This password is too common"}
    good = {"old_password": "blue-river-42", "new_password": "green-hill-77"}
    assert (await api.patch(url, json=good)).status_code == 204
    after = await stored_hash()
    assert after != before and after.startswith("$argon2id$")
    check = {"email": "asha@example.com", "password": "green-hill-77"}
    assert (await api.post("/auth/check", json=check)).status_code == 200
    assert (await api.patch("/users/9/password", json=good)).status_code == 404


async def test_find_by_email(api: httpx.AsyncClient) -> None:
    await api.post("/users", json=ASHA)
    found = await api.get("/users", params={"email": "ASHA@Example.com"})
    assert found.json()["id"] == 1 and "password_hash" not in found.json()
    assert (await api.get("/users", params={"email": "nobody@x.com"})).status_code == 404
