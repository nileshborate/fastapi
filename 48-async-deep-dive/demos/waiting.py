# Run: python -m demos.waiting
# 10 requests at the same time, each "waits" 0.5 seconds. How long until all 10 are answered?
import asyncio

from demos.common import serve, together

ENDPOINTS = [
    ("async def + await asyncio.sleep", "/io/async-await"),
    ("def + time.sleep (threadpool)", "/io/sync"),
    ("async def + run_in_threadpool", "/io/offload"),
    ("async def + time.sleep  (BAD)", "/io/async-blocking"),
]


async def main() -> None:
    async with serve() as client:
        print("10 requests x 0.5 s of waiting each\n")
        for label, path in ENDPOINTS:
            seconds = await together(client, f"{path}?seconds=0.5", 10)
            print(f"{label:<34} all 10 answered after {seconds:5.2f} s")


if __name__ == "__main__":
    asyncio.run(main())
