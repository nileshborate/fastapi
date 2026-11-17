# An error with context, a request id the client sends, events with fields, secrets hidden
import asyncio
import json
import os

os.environ["LOG_LEVEL"] = "DEBUG"                   # show the debug line too

from demos.common import LINES, serve  # noqa: E402

CARD = {"email": "asha@example.com", "course_id": 2, "card_number": "4111111111111111"}


async def main() -> None:
    async with serve() as client:
        r = await client.get("/boom", headers={"X-Request-ID": "support-42"})
        print("GET /boom ->", r.status_code, r.json())
        for body in (CARD, CARD, CARD | {"course_id": 9}):
            r = await client.post("/enrollments", json=body)
            print("POST /enrollments ->", r.status_code, r.json(), r.headers["x-request-id"])
    for e in map(json.loads, LINES):
        e.pop("ts"), e.pop("service"), e.pop("logger")
        tb = e.pop("traceback", None)
        print(e)
        if tb:
            print("    traceback, last line:", tb.splitlines()[-1])


asyncio.run(main())
