# Run: python -m demos.limits   (after: alembic upgrade head)
# Requests that are too BIG: a huge body, a long string, a huge page, extra fields
import asyncio

from app.database import engine
from demos.common import asha, clean, client


def short(response) -> str:
    body = response.json()
    if isinstance(body.get("detail"), list):                  # a 422: show the first problem
        problem = body["detail"][0]
        return f"{problem['loc'][-1]}: {problem['msg']}"
    if "detail" in body:
        return body["detail"]
    return f"created: {body['title']}, owner_id {body['owner_id']}"


async def main() -> None:
    await clean()
    async with client() as c:
        headers = await asha(c)
        cases = [
            ("1. a 1 MB body", "POST", "/courses", {"title": "x" * 1_000_000, "fee": 1}),
            ("2. a 3,000 character title", "POST", "/courses", {"title": "x" * 3000, "fee": 1}),
            ("3. a fee of one billion", "POST", "/courses",
             {"title": "SQL Basics", "fee": 10**9}),
            ("4. owner_id in the body", "POST", "/courses",
             {"title": "SQL Basics", "fee": 99, "owner_id": 7}),
            ("5. limit=1000000", "GET", "/courses?limit=1000000", None),
            ("6. a 500 character search", "GET", "/courses?q=" + "a" * 500, None),
            ("7. a normal course", "POST", "/courses", {"title": "SQL Basics", "fee": 199}),
        ]
        for label, method, url, body in cases:
            r = await c.request(method, url, json=body, headers=headers)
            print(f"{label:<28} {r.status_code}  {short(r)[:60]}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
