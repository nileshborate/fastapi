# Helpers for the demos: a clean database and an in-process client
import httpx
from sqlalchemy import delete

from app.database import SessionLocal
from app.main import app
from app.models import RefreshToken, User


async def clean() -> None:
    async with SessionLocal() as db:
        await db.execute(delete(RefreshToken))
        await db.execute(delete(User))
        await db.commit()


def client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def login(c: httpx.AsyncClient, email: str = "asha@example.com") -> dict:
    await c.post("/users", json={"email": email, "full_name": "Asha Patil",
                                 "password": "blue-river-42"})
    form = {"username": email, "password": "blue-river-42"}
    return (await c.post("/token", data=form)).json()


def short(token: str) -> str:
    return token[:12] + "..." + token[-6:]
