# Forgot + reset: the same answer for every email, one-time links, expiry
from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionLocal
from app.links import hash_token, issue_link
from app.models import LinkToken, User
from tests.conftest import ASHA, FakeMailer, login, register


def forgot(client: TestClient, email: str = ASHA["email"]):
    return client.post("/password/forgot", json={"email": email})


def test_known_and_unknown_look_the_same(client: TestClient, mailer: FakeMailer) -> None:
    register(client)
    known, unknown = forgot(client), forgot(client, "nobody@example.com")
    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    assert [e.subject for e in mailer.sent] == ["Confirm your email", "Reset your password"]


def test_reset_works_once(client: TestClient, mailer: FakeMailer) -> None:
    register(client)
    forgot(client)
    body = {"token": mailer.last_token(), "new_password": "green-hill-77"}
    assert client.post("/password/reset", json=body).status_code == 200
    assert login(client).status_code == 401                       # the old password
    assert login(client, "green-hill-77").status_code == 200      # verified by the link
    assert client.post("/password/reset", json=body).status_code == 400


def test_only_the_newest_link_works(client: TestClient, mailer: FakeMailer) -> None:
    register(client)
    forgot(client)
    first = mailer.last_token()
    forgot(client)
    body = {"token": first, "new_password": "green-hill-77"}
    assert client.post("/password/reset", json=body).status_code == 400
    body["token"] = mailer.last_token()
    assert client.post("/password/reset", json=body).status_code == 200


def test_a_verify_link_cant_reset(client: TestClient, mailer: FakeMailer) -> None:
    register(client)
    body = {"token": mailer.last_token(), "new_password": "green-hill-77"}
    assert client.post("/password/reset", json=body).status_code == 400   # wrong purpose


def test_expired_link_and_the_database(client: TestClient, mailer: FakeMailer) -> None:
    register(client)

    async def expired_link() -> tuple[str, list[str]]:
        async with SessionLocal() as db:
            user = await db.scalar(select(User))
            raw = await issue_link(db, user, "reset", timedelta(minutes=-1))
            await db.commit()
            return raw, list(await db.scalars(select(LinkToken.token_hash)))
    raw, stored = client.portal.call(expired_link)
    body = {"token": raw, "new_password": "green-hill-77"}
    assert client.post("/password/reset", json=body).status_code == 400
    assert raw not in stored and hash_token(raw) in stored          # only the hash is stored
