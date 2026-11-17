# Run: python -m demos.sunset      - the sunset date has passed: v1 answers 410 Gone
import asyncio
import os

os.environ["V1_SUNSET_AT"] = "2026-11-01T00:00:00Z"        # pretend: v1 ended already

from demos.common import serve  # noqa: E402


async def main() -> None:
    async with serve() as client:
        response = await client.get("/v1/courses/1")
        print(f"GET /v1/courses/1 -> {response.status_code} {response.json()}")
        response = await client.get("/v2/courses/1")
        print(f"GET /v2/courses/1 -> {response.status_code} {response.json()}")


asyncio.run(main())
