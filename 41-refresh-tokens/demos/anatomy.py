# Run: python -m demos.anatomy   (after: alembic upgrade head)
# Log in once - and look INSIDE the two tokens we get back
import asyncio
from datetime import UTC, datetime

import jwt

from app.database import engine
from demos.common import clean, client, login


def show(name: str, token: str) -> None:
    claims = jwt.decode(token, options={"verify_signature": False})    # just to LOOK
    life = claims["exp"] - claims["iat"]
    print(f"{name}: {len(token)} characters")
    for key, value in claims.items():
        if key in ("iat", "exp"):
            value = datetime.fromtimestamp(value, UTC).strftime("%Y-%m-%d %H:%M")
        print(f"   {key:<5} {value}")
    lives = f"{life // 60} minutes" if life < 86400 else f"{life // 86400} days"
    print(f"   lives {lives}")


async def main() -> None:
    await clean()
    async with client() as c:
        pair = await login(c)
    print("keys in the answer:", list(pair))
    show("access token ", pair["access_token"])
    show("refresh token", pair["refresh_token"])
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
