# Run: python -m demos.brute_force   (after: alembic upgrade head)
# An attacker tries passwords for Asha - how far does he get?
import asyncio

from app.database import engine
from demos.common import PASSWORD, asha, clean, client


async def main() -> None:
    await clean()
    async with client() as c:
        await asha(c)                                     # try 1: Asha's own login
        print("try 1: Asha logs in herself      200 TOKEN")
        guesses = ["123456", "password", "qwerty", "asha1990", "letmein", PASSWORD]
        for n, guess in enumerate(guesses, start=2):
            r = await c.post("/token", data={"username": "asha@example.com", "password": guess})
            answer = "TOKEN" if r.status_code == 200 else r.json()["detail"]
            retry = r.headers.get("retry-after")
            print(f"try {n}: {guess:<26} {r.status_code} {answer}"
                  + (f"  Retry-After: {retry}" if retry else ""))
        r = await c.post("/token", data={"username": "ravi@example.com", "password": "123456"})
        print(f"{'another email':<33} {r.status_code} {r.json()['detail']}  <- its own counter")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
