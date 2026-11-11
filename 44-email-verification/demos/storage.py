# Run: python -m demos.storage   (after: alembic upgrade head)
# What is in the email - and what is in the database? And: only the NEWEST link works
import asyncio

from sqlalchemy import select

from app.database import SessionLocal, engine
from app.links import hash_token
from app.models import LinkToken
from demos.common import clean, client, show, token_from_last_email


async def main() -> None:
    await clean()
    async with client() as c:
        await c.post("/users", json={"email": "asha@example.com", "full_name": "Asha Patil",
                                     "password": "blue-river-42"})
        token = token_from_last_email()
        print("in the email   :", token, f"({len(token)} characters)")
        print("its SHA-256    :", hash_token(token))
        async with SessionLocal() as db:
            row = await db.scalar(select(LinkToken))
            print("in the database:", row.token_hash, "| purpose:", row.purpose)
            print("the token itself in the database?", token == row.token_hash)

        await c.post("/password/forgot", json={"email": "asha@example.com"})
        first = token_from_last_email()
        await c.post("/password/forgot", json={"email": "asha@example.com"})
        second = token_from_last_email()
        reset = {"token": first, "new_password": "green-hill-77"}
        print()
        show("the FIRST reset link", await c.post("/password/reset", json=reset))
        reset["token"] = second
        show("the SECOND (newest) reset link", await c.post("/password/reset", json=reset))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
