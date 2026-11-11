# Run: python -m demos.forgot   (after: alembic upgrade head)
# "Forgot password" for a known and an unknown email - can you tell them apart?
import asyncio
from datetime import timedelta

from sqlalchemy import select

from app.database import SessionLocal, engine
from app.links import issue_link
from app.mailer import mailer
from app.models import User
from demos.common import clean, client, show, token_from_last_email


async def main() -> None:
    await clean()
    async with client() as c:
        await c.post("/users", json={"email": "asha@example.com", "full_name": "Asha Patil",
                                     "password": "blue-river-42"})
        mailer.outbox.clear()
        for step, email in (("1. forgot: asha@example.com", "asha@example.com"),
                            ("2. forgot: nobody@example.com", "nobody@example.com")):
            show(step, await c.post("/password/forgot", json={"email": email}))
        print(f"   emails sent: {len(mailer.outbox)} -> to {mailer.outbox[0].to}")

        token = token_from_last_email()
        reset = {"token": token, "new_password": "green-hill-77"}
        show("3. POST /password/reset", await c.post("/password/reset", json=reset))
        old = {"username": "asha@example.com", "password": "blue-river-42"}
        new = {"username": "asha@example.com", "password": "green-hill-77"}
        print(f"{'4. log in: old password / new password':<40} "
              f"{(await c.post('/token', data=old)).status_code} / "
              f"{(await c.post('/token', data=new)).status_code}")
        show("5. the SAME link again", await c.post("/password/reset", json=reset))

        async with SessionLocal() as db:                       # a link that is already old
            asha = await db.scalar(select(User).where(User.email == "asha@example.com"))
            expired = await issue_link(db, asha, "reset", timedelta(minutes=-1))
            await db.commit()
        reset = {"token": expired, "new_password": "yellow-sun-55"}
        show("6. an expired link", await c.post("/password/reset", json=reset))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
