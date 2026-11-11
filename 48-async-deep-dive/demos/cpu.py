# Run: python -m demos.cpu
# 4 CPU-heavy requests at the same time: inline, in a thread, in a process
import asyncio
import os

from demos.common import serve, timed_get, together


async def main() -> None:
    async with serve() as client:
        one = await timed_get(client, "/cpu/inline?limit=300000")
        print(f"this computer has {os.cpu_count()} CPU cores")
        print(f"{'ONE request alone':<38} {one:5.2f} s\n")
        for label, path in (("async def, inline (BAD)", "/cpu/inline"),
                            ("run_in_threadpool (GIL)", "/cpu/thread"),
                            ("ProcessPoolExecutor (2 workers)", "/cpu/process")):
            seconds = await together(client, f"{path}?limit=300000", 4)
            print(f"4 x {label:<34} {seconds:5.2f} s")


if __name__ == "__main__":
    asyncio.run(main())
