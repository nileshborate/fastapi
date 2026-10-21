# Video 5 - Async/Await and the Event Loop
# Nilesh Technology - FastAPI Mastery: Zero to Production
#
# Same job done two ways: "download" 3 courses, each takes 1 second of waiting (I/O).
# Run:  python sync_vs_async.py

import asyncio
import time


# ---------- Synchronous: wait for each one, one after another ----------
def fetch_course_sync(course_id: int) -> str:
    time.sleep(1)                      # pretend: database / API call
    return f"course {course_id}"


def main_sync() -> None:
    start = time.perf_counter()
    results = [fetch_course_sync(i) for i in (1, 2, 3)]
    print("sync :", results, f"{time.perf_counter() - start:.1f}s")    # ~3.0s


# ---------- Asynchronous: start all three, wait together ----------
async def fetch_course(course_id: int) -> str:
    await asyncio.sleep(1)             # non-blocking wait - the loop runs others
    return f"course {course_id}"


async def main_async() -> None:
    start = time.perf_counter()
    results = await asyncio.gather(fetch_course(1), fetch_course(2), fetch_course(3))
    print("async:", results, f"{time.perf_counter() - start:.1f}s")    # ~1.0s


# ---------- A coroutine does nothing until it is awaited ----------
async def show_coroutine() -> None:
    c = fetch_course(7)
    print("calling fetch_course(7) gives:", type(c).__name__)   # coroutine
    print("awaiting it gives:", await c)


if __name__ == "__main__":
    main_sync()
    asyncio.run(main_async())
    asyncio.run(show_coroutine())
