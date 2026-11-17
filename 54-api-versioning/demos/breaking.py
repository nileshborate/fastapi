# Run: python -m demos.breaking    - an OLD mobile app written for v1 - what if we changed v1?
import asyncio

from demos.common import serve


def old_app_screen(course: dict) -> str:
    """code inside an app that is already installed on 10,000 phones"""
    return f"{course['name'].upper()} - Rs {course['price'] * 2} for 2 seats"


async def main() -> None:
    async with serve() as client:
        v1 = (await client.get("/v1/courses/2")).json()
        print("GET /v1/courses/2 ->", v1)
        print("old app on v1     ->", old_app_screen(v1))

        v2 = (await client.get("/v2/courses/2")).json()
        print("GET /v2/courses/2 ->", v2)
        try:
            print("old app on v2     ->", old_app_screen(v2))
        except Exception as error:                        # what users would see: a crash
            print("old app on v2     ->", type(error).__name__, error)
        v2["name"] = v2["title"]
        try:
            old_app_screen(v2)
        except Exception as error:
            print("... and next      ->", type(error).__name__, error)


asyncio.run(main())
