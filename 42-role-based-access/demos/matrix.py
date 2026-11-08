# Run: python -m demos.matrix   (after: alembic upgrade head)
# The same 8 requests - sent by a guest, a student, a teacher and an admin
import asyncio

from app.database import engine
from demos.common import clean, client, three_users


async def main() -> None:
    await clean()
    async with client() as c:
        users, ids = await three_users(c)
        ravis = (await c.post("/courses", json={"title": "FastAPI Basics", "fee": 299},
                              headers=users["teacher"])).json()["id"]
        new = {"title": "SQL Basics", "fee": 199}
        requests = [
            ("GET    /courses", "GET", "/courses", None),
            ("POST   /courses", "POST", "/courses", new),            # teacher, then admin
            ("PATCH  Ravi's course", "PATCH", f"/courses/{ravis}", {"fee": 349}),
            ("PATCH  Asha's course", "PATCH", f"/courses/{ravis + 2}", {"fee": 249}),
            ("POST   .../enroll", "POST", f"/courses/{ravis}/enroll", None),
            ("GET    /admin/users", "GET", "/admin/users", None),
            ("PATCH  Meera's role", "PATCH", f"/admin/users/{ids['meera']}/role",
             {"role": "student"}),
            ("DELETE Ravi's 2nd course", "DELETE", f"/courses/{ravis + 1}", None),
        ]
        print(f"{'':<26}" + "".join(f"{who:>9}" for who in users))
        for label, method, url, body in requests:
            codes = []
            for headers in users.values():
                response = await c.request(method, url, json=body, headers=headers)
                codes.append(response.status_code)
            print(f"{label:<26}" + "".join(f"{code:>9}" for code in codes))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
