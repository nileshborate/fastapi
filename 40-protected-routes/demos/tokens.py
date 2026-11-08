# Run: python -m demos.tokens   (after: alembic upgrade head)
# Seven tokens against GET /me - what does get_current_active_user answer?
import asyncio

import httpx
import jwt
from sqlalchemy import delete, update

from app.database import SessionLocal, engine
from app.main import app
from app.models import Course, User
from app.security import create_access_token


async def main() -> None:
    async with SessionLocal() as db:                       # a clean start for the demo
        await db.execute(delete(Course))
        await db.execute(delete(User))
        await db.commit()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        for email in ("asha@example.com", "ravi@example.com"):
            await client.post("/users", json={"email": email, "full_name": email[:4].title(),
                                              "password": "blue-river-42"})
        form = {"username": "asha@example.com", "password": "blue-river-42"}
        asha = (await client.post("/token", data=form)).json()["access_token"]
        form["username"] = "ravi@example.com"
        ravi = (await client.post("/token", data=form)).json()["access_token"]
        async with SessionLocal() as db:                   # Ravi's account gets blocked
            await db.execute(update(User).where(User.email == "ravi@example.com")
                             .values(is_active=False))
            await db.commit()
        asha_id = jwt.decode(asha, options={"verify_signature": False})["sub"]
        cases = [
            ("1. no token", None),
            ("2. garbage", "abc.def.ghi"),
            ("3. expired", create_access_token(int(asha_id), minutes=-1)),
            ("4. other secret", jwt.encode({"sub": asha_id, "exp": 9999999999}, "x" * 40)),
            ("5. user deleted", create_access_token(999)),
            ("6. inactive user", ravi),
            ("7. Asha, valid", asha),
        ]
        for label, token in cases:
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            response = await client.get("/me", headers=headers)
            print(f"{label:<18} {response.status_code}  {response.json()}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
