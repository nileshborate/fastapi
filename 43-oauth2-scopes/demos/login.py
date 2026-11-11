# Run: python -m demos.login   (after: alembic upgrade head)
# The client ASKS for scopes - the server decides what the token really gets
import asyncio

from app.database import engine
from demos.common import clean, client, login, three_users

ASKS = [
    ("asha@example.com", None),                    # nothing asked -> all her role allows
    ("asha@example.com", "courses:read"),          # a read-only token for a report script
    ("ravi@example.com", None),
    ("meera@example.com", "me users:manage"),      # asks too much -> gets less
    ("meera@example.com", "me superpower"),        # an unknown scope -> 400
]


async def main() -> None:
    await clean()
    async with client() as c:
        await three_users(c)
        print(f"{'who':<9} {'asked for':<20} answer")
        for email, scope in ASKS:
            response = await login(c, email, scope)
            body = response.json()
            got = f"scope: {body['scope']!r}" if response.status_code == 200 else body
            who = email.split("@")[0]
            print(f"{who:<9} {scope or '(nothing)':<20} {response.status_code} {got}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
