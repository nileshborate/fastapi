# Run: python -m demos.client_flow   (after: alembic upgrade head)
# What a frontend does: the access token expired -> refresh -> try again
import asyncio

from app.database import engine
from app.security import create_access_token
from demos.common import clean, client, login


async def main() -> None:
    await clean()
    async with client() as c:
        pair = await login(c)
        # pretend 15 minutes went by: an access token that is already expired
        pair["access_token"] = create_access_token(1, version=0, minutes=-1)

        r = await c.get("/me", headers={"Authorization": f"Bearer {pair['access_token']}"})
        print("1. GET /me with the old access token ", r.status_code, r.json())
        if r.status_code == 401:
            r = await c.post("/token/refresh", json={"refresh_token": pair["refresh_token"]})
            print("2. POST /token/refresh               ", r.status_code, "a new pair")
            pair = r.json()
            r = await c.get("/me", headers={"Authorization": f"Bearer {pair['access_token']}"})
            print("3. GET /me again                     ", r.status_code, r.json()["email"])
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
