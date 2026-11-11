# Run: python -m demos.downgrade   (after: alembic upgrade head)
# Ravi's token still SAYS "courses:write" - but his role changed
import asyncio

import jwt

from app.database import engine
from demos.common import bearer, clean, client, login, three_users


async def main() -> None:
    await clean()
    async with client() as c:
        ids = await three_users(c)
        ravi_login = await login(c, "ravi@example.com")
        ravi, asha = bearer(ravi_login), bearer(await login(c, "asha@example.com"))
        token = ravi_login.json()["access_token"]
        claims = jwt.decode(token, options={"verify_signature": False})
        print("Ravi's token scope:", claims["scope"])
        course = {"title": "Docker Basics", "fee": 399}

        r = await c.post("/courses", json=course, headers=ravi)
        print("1. Ravi (teacher): POST /courses        ", r.status_code, r.json()["title"])
        r = await c.patch(f"/admin/users/{ids['ravi']}/role", json={"role": "student"},
                          headers=asha)
        print("2. Asha: Ravi -> student                 ", r.status_code, r.json()["role"])
        r = await c.post("/courses", json=course, headers=ravi)
        print("3. Ravi, the SAME token: POST /courses  ", r.status_code, r.json())
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
