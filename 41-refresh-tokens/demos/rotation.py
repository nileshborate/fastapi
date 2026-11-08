# Run: python -m demos.rotation   (after: alembic upgrade head)
# Refresh twice, then a "thief" replays an old refresh token
import asyncio

from sqlalchemy import select

from app.database import SessionLocal, engine
from app.models import RefreshToken
from demos.common import clean, client, login, short


async def refresh(c, token: str, who: str) -> dict:
    response = await c.post("/token/refresh", json={"refresh_token": token})
    body = response.json()
    shown = short(body["refresh_token"]) if response.status_code == 200 else body
    print(f"{who:<26} {response.status_code}  {shown}")
    return body


async def main() -> None:
    await clean()
    async with client() as c:
        first = await login(c)
        print(f"{'1. login':<26} 200  {short(first['refresh_token'])}")
        second = await refresh(c, first["refresh_token"], "2. refresh with token 1")
        third = await refresh(c, second["refresh_token"], "3. refresh with token 2")
        await refresh(c, first["refresh_token"], "4. thief replays token 1")
        await refresh(c, third["refresh_token"], "5. Asha uses token 3")
    async with SessionLocal() as db:
        print("\nthe refresh_tokens table:")
        for row in await db.scalars(select(RefreshToken).order_by(RefreshToken.id)):
            state = "REVOKED" if row.revoked_at else "alive"
            nxt = f"-> replaced by {row.replaced_by[:8]}" if row.replaced_by else ""
            print(f"   {row.id}  jti={row.jti[:8]}  {state:<7} {nxt}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
