# Helpers for the demos: a clean database, an in-process client, three users
import httpx
from sqlalchemy import delete

from app.database import SessionLocal
from app.main import app
from app.make_admin import make_admin
from app.models import Course, Enrollment, User


async def clean() -> None:
    async with SessionLocal() as db:
        for model in (Enrollment, Course, User):
            await db.execute(delete(model))
        await db.commit()


def client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def register_and_login(c: httpx.AsyncClient, email: str, name: str) -> tuple[dict, int]:
    """returns the Authorization header and the user's id"""
    user = await c.post("/users", json={"email": email, "full_name": name,
                                        "password": "blue-river-42"})
    form = {"username": email, "password": "blue-river-42"}
    token = (await c.post("/token", data=form)).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, user.json()["id"]


async def three_users(c: httpx.AsyncClient) -> tuple[dict[str, dict], dict[str, int]]:
    """Asha: admin (the script) · Ravi: teacher (Asha promotes him) · Meera: student"""
    asha, asha_id = await register_and_login(c, "asha@example.com", "Asha")
    ravi, ravi_id = await register_and_login(c, "ravi@example.com", "Ravi")
    meera, meera_id = await register_and_login(c, "meera@example.com", "Meera")
    await make_admin("asha@example.com")
    await c.patch(f"/admin/users/{ravi_id}/role", json={"role": "teacher"}, headers=asha)
    headers = {"guest": {}, "student": meera, "teacher": ravi, "admin": asha}
    return headers, {"asha": asha_id, "ravi": ravi_id, "meera": meera_id}
