# Run: python -m demos.matrix   (after: alembic upgrade head)
# Five tokens against four endpoints - and the header that says WHY
import asyncio

from app.database import engine
from demos.common import bearer, clean, client, login, three_users


async def main() -> None:
    await clean()
    async with client() as c:
        await three_users(c)
        tokens = {
            "meera (all)": bearer(await login(c, "meera@example.com")),
            "ravi (all)": bearer(await login(c, "ravi@example.com")),
            "ravi (read)": bearer(await login(c, "ravi@example.com", "courses:read")),
            "asha (all)": bearer(await login(c, "asha@example.com")),
            "asha (read)": bearer(await login(c, "asha@example.com", "courses:read")),
        }
        requests = [("GET /me", "GET", "/me"), ("GET /courses", "GET", "/courses"),
                    ("POST /courses", "POST", "/courses"),
                    ("GET /admin/users", "GET", "/admin/users")]
        print(f"{'':<17}" + "".join(f"{name:>13}" for name in tokens))
        for label, method, url in requests:
            body = {"title": "SQL Basics", "fee": 199} if method == "POST" else None
            codes = [(await c.request(method, url, json=body, headers=h)).status_code
                     for h in tokens.values()]
            print(f"{label:<17}" + "".join(f"{code:>13}" for code in codes))

        response = await c.post("/courses", json={"title": "SQL Basics", "fee": 199},
                                headers=tokens["asha (read)"])
        print("\nasha (read): POST /courses ->", response.status_code, response.json())
        print("WWW-Authenticate:", response.headers["www-authenticate"])
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
