# Run: python -m demos.signup   (after: alembic upgrade head)
# Register -> the email -> log in too early -> verify -> log in -> the same link again
import asyncio

from app.database import engine
from app.mailer import mailer
from demos.common import clean, client, show, token_from_last_email


async def main() -> None:
    await clean()
    async with client() as c:
        body = {"email": "asha@example.com", "full_name": "Asha Patil",
                "password": "blue-river-42"}
        show("1. POST /users", await c.post("/users", json=body))
        email = mailer.outbox[-1]
        print(f"   the email: to={email.to} subject={email.subject!r}")
        print("   " + email.body.splitlines()[1])
        form = {"username": "asha@example.com", "password": "blue-river-42"}
        show("2. POST /token (not verified yet)", await c.post("/token", data=form))
        token = token_from_last_email()
        show("3. POST /verify-email", await c.post("/verify-email", json={"token": token}))
        r = await c.post("/token", data=form)
        token_start = r.json()["access_token"][:12]
        print(f"{'4. POST /token':<40} {r.status_code} access_token: {token_start}...")
        show("5. the SAME link again", await c.post("/verify-email", json={"token": token}))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
