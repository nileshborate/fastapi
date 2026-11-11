# Helpers for the demos: a clean database and an in-process client
import httpx
from fastapi import FastAPI
from sqlalchemy import delete

from app.database import SessionLocal
from app.main import app as default_app
from app.models import Course, User

PASSWORD = "blue-river-42"


async def clean() -> None:
    async with SessionLocal() as db:
        await db.execute(delete(Course))
        await db.execute(delete(User))
        await db.commit()
    for limiter in ("login_limiter", "write_limiter", "ip_limiter"):
        getattr(default_app.state, limiter).reset()


def client(app: FastAPI = default_app, base_url: str = "http://localhost") -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    return httpx.AsyncClient(transport=transport, base_url=base_url)


async def asha(c: httpx.AsyncClient) -> dict[str, str]:
    await c.post("/users", json={"email": "asha@example.com", "full_name": "Asha Patil",
                                 "password": PASSWORD})
    form = {"username": "asha@example.com", "password": PASSWORD}
    token = (await c.post("/token", data=form)).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
