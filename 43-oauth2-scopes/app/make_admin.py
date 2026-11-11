# Run: python -m app.make_admin asha@example.com
# The FIRST admin can't come from the API - nobody is admin yet. So: a script on the server.
import asyncio
import sys

from sqlalchemy import select

from app.database import SessionLocal, engine
from app.models import User
from app.roles import Role


async def make_admin(email: str) -> str:
    async with SessionLocal() as db:
        user = await db.scalar(select(User).where(User.email == email.lower()))
        if user is None:
            return f"no user with the email {email} - register first"
        user.role = Role.ADMIN
        await db.commit()
        return f"{user.email} is now an admin"


if __name__ == "__main__":
    print(asyncio.run(make_admin(sys.argv[1])))
    asyncio.run(engine.dispose())
