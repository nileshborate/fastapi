# Run: python -m demos.disconnect
# The user closes the tab after 2 progress events. Does the server keep working?
import asyncio

from app.routers import live
from demos.common import log, serve


async def main() -> None:
    async with serve() as client:
        received = 0
        async with client.stream("GET", "/jobs/tab-closed/progress?delay=0.5") as response:
            async for line in response.aiter_lines():
                if line.startswith("id:"):
                    received += 1
                    log(f"client got {line}")
                if received == 2:
                    log("client closes the tab")
                    break                                    # leaving "async with" closes it
        await asyncio.sleep(0.3)
        log(f"server: {live.cleanups}")
        log("a full job has 5 steps - the server stopped working for the closed tab")


if __name__ == "__main__":
    asyncio.run(main())
