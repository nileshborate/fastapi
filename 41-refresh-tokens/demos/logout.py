# Run: python -m demos.logout   (after: alembic upgrade head)
# Logout kills the refresh token - but what about the ACCESS token?
import asyncio

from app.database import engine
from demos.common import clean, client, login


async def main() -> None:
    await clean()
    async with client() as c:
        phone = await login(c)                          # two devices, two logins
        laptop = await login(c)
        bearer = {"Authorization": f"Bearer {phone['access_token']}"}

        r = await c.post("/logout", json={"refresh_token": phone["refresh_token"]})
        print("1. phone: POST /logout              ", r.status_code)
        r = await c.post("/token/refresh", json={"refresh_token": phone["refresh_token"]})
        print("2. phone: refresh after logout      ", r.status_code, r.json())
        r = await c.get("/me", headers=bearer)
        print("3. phone: OLD access token, GET /me ", r.status_code, "<- still works!")

        laptop_bearer = {"Authorization": f"Bearer {laptop['access_token']}"}
        r = await c.post("/logout/all", headers=laptop_bearer)
        print("4. laptop: POST /logout/all         ", r.status_code)
        r = await c.get("/me", headers=bearer)
        print("5. phone: OLD access token, GET /me ", r.status_code, r.json())
        r = await c.post("/token/refresh", json={"refresh_token": laptop["refresh_token"]})
        print("6. laptop: refresh                  ", r.status_code, r.json())
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
