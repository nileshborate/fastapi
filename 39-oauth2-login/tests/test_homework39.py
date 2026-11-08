# Homework answer (Video 39): inactive users can't log in, expires_in in the answer
from fastapi.testclient import TestClient
from sqlalchemy import update

from app.database import SessionLocal
from app.models import User


def deactivate(client: TestClient, email: str) -> None:
    async def run() -> None:
        async with SessionLocal() as db:
            await db.execute(update(User).where(User.email == email).values(is_active=False))
            await db.commit()
    client.portal.call(run)         # runs on the APP's event loop (asyncpg needs that)


def test_expires_in(client: TestClient) -> None:
    form = {"username": "asha@example.com", "password": "blue-river-42"}
    assert client.post("/token", data=form).json()["expires_in"] == 900


def test_inactive_user_cannot_log_in(client: TestClient) -> None:
    deactivate(client, "asha@example.com")
    form = {"username": "asha@example.com", "password": "blue-river-42"}
    response = client.post("/token", data=form)
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect email or password"}     # the same message
