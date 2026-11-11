# Helpers for the demos: a clean database, an in-process client, and the outbox
import re

import httpx
from sqlalchemy import delete

from app.database import SessionLocal
from app.mailer import mailer
from app.main import app
from app.models import LinkToken, User


async def clean() -> None:
    async with SessionLocal() as db:
        await db.execute(delete(LinkToken))
        await db.execute(delete(User))
        await db.commit()
    mailer.outbox.clear()


def client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


def token_from_last_email() -> str:
    """what the user does: open the email, click the link -> the token in the URL"""
    return re.search(r"token=([\w-]+)", mailer.outbox[-1].body).group(1)


def show(step: str, response: httpx.Response) -> None:
    print(f"{step:<40} {response.status_code} {response.json()}")
