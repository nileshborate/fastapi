# The fix: JSON lines with a request id - then FIND one request, and ANSWER questions
import asyncio
import json

from demos.common import LINES, serve


async def main() -> None:
    async with serve() as client:
        responses = await asyncio.gather(*(client.get(f"/reports/{n}") for n in (1, 2, 3)))
        await client.get("/reports/abc")                       # a 422
    ids = {r.json()["course_id"]: r.headers["x-request-id"] for r in responses}
    print("X-Request-ID per course:", ids)
    print("\n--- the raw log, first 3 lines ---")
    for line in LINES[:3]:
        print(line)

    entries = [json.loads(line) for line in LINES]            # every line is JSON
    print(f"\n--- find ONE request: request_id == {ids[2]} ---")
    for e in entries:
        if e["request_id"] == ids[2]:
            print(f"  {e['event']:<16} {e.get('step', '')}{e.get('duration_ms', '')}")
    done = [e for e in entries if e["event"] == "request.done"]
    slowest = max(done, key=lambda e: e["duration_ms"])
    print("\n--- questions ---")
    print("requests:", len(done), "· by status:",
          {s: sum(e["status"] == s for e in done) for s in sorted({e["status"] for e in done})})
    print("slowest:", slowest["path"], slowest["duration_ms"], "ms ·", slowest["request_id"])


asyncio.run(main())
