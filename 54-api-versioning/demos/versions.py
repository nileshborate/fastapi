# Run: python -m demos.versions    - two versions, ONE store, the deprecation headers, Accept
import asyncio

from demos.common import serve

V2 = "application/vnd.coursehub.v2+json"


async def main() -> None:
    async with serve() as client:
        created = await client.post("/v1/courses", json={"name": "Git", "teacher": "Meera",
                                                         "price": 199})
        print(f"POST /v1/courses   -> {created.status_code} {created.json()}")
        print(f"GET  /v2/courses/4 -> {(await client.get('/v2/courses/4')).json()}")

        response = await client.get("/v1/courses/1", headers={"X-Client-Id": "android-3.1"})
        for name in ("deprecation", "sunset", "link"):
            print(f"v1 {name:11} : {response.headers[name]}")
        v2 = await client.get("/v2/courses/1")
        print(f"v2 deprecation : {v2.headers.get('deprecation')}")

        old = (await client.get("/courses/2")).json()
        new = await client.get("/courses/2", headers={"Accept": V2})
        print(f"GET /courses/2 (no Accept)   -> {old}")
        print(f"GET /courses/2 (Accept: v2)  -> {new.json()}   Vary: {new.headers['vary']}")

        await client.get("/v1/courses", headers={"X-Client-Id": "android-3.1"})
        await client.get("/v1/courses", headers={"X-Client-Id": "partner-acme"})
        print(f"GET /admin/v1-usage -> {(await client.get('/admin/v1-usage')).json()}")


asyncio.run(main())
