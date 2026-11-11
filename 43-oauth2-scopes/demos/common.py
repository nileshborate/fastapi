# Helpers for the demos: a clean database, a client, three users, and logins with scopes
import httpx
from sqlalchemy import delete

from app.database import SessionLocal
from app.main import app
from app.make_admin import make_admin
from app.models import Course, User


async def clean() -> None:
    async with SessionLocal() as db:
        await db.execute(delete(Course))
        await db.execute(delete(User))
        await db.commit()


def client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def login(c: httpx.AsyncClient, email: str, scope: str | None = None) -> httpx.Response:
    form = {"username": email, "password": "blue-river-42"}
    if scope is not None:
        form["scope"] = scope                         # the OAuth2 form field: "a b c"
    return await c.post("/token", data=form)


def bearer(response: httpx.Response) -> dict[str, str]:
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def three_users(c: httpx.AsyncClient) -> dict[str, int]:
    """Asha: admin · Ravi: teacher · Meera: student - returns their ids"""
    ids = {}
    for name in ("asha", "ravi", "meera"):
        body = {"email": f"{name}@example.com", "full_name": name.title(),
                "password": "blue-river-42"}
        user = await c.post("/users", json=body)
        ids[name] = user.json()["id"]
    await make_admin("asha@example.com")
    asha = bearer(await login(c, "asha@example.com"))
    await c.patch(f"/admin/users/{ids['ravi']}/role", json={"role": "teacher"}, headers=asha)
    return ids
