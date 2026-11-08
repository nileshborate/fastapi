# Run: python -m demos.promote   (after: alembic upgrade head)
# Meera's token stays the SAME - but her role changes in the database
import asyncio

import jwt

from app.database import engine
from demos.common import clean, client, three_users


async def main() -> None:
    await clean()
    async with client() as c:
        users, ids = await three_users(c)
        meera, asha = users["student"], users["admin"]
        token = meera["Authorization"].removeprefix("Bearer ")
        print("Meera's token claims:", jwt.decode(token, options={"verify_signature": False}))
        course = {"title": "Python for Kids", "fee": 99}

        r = await c.post("/courses", json=course, headers=meera)
        print("1. Meera (student): POST /courses       ", r.status_code, r.json())
        r = await c.patch(f"/admin/users/{ids['meera']}/role", json={"role": "teacher"},
                          headers=asha)
        print("2. Asha (admin): Meera -> teacher        ", r.status_code, r.json()["role"])
        r = await c.post("/courses", json=course, headers=meera)
        print("3. Meera, the SAME token: POST /courses ", r.status_code, r.json()["title"])
        r = await c.patch(f"/admin/users/{ids['asha']}/role", json={"role": "student"},
                          headers=asha)
        print("4. Asha changes her OWN role             ", r.status_code, r.json())
        r = await c.patch(f"/admin/users/{ids['meera']}/role", json={"role": "superuser"},
                          headers=asha)
        print("5. an unknown role                       ", r.status_code,
              r.json()["detail"][0]["msg"])
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
