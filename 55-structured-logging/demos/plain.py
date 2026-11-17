# The problem: 3 requests at the same time, plain text logs - which line belongs to which?
import asyncio
import os

os.environ["LOG_JSON"] = "false"

from demos.common import LINES, serve  # noqa: E402


async def main() -> None:
    async with serve() as client:
        await asyncio.gather(*(client.get(f"/reports/{n}") for n in (1, 2, 3)))
    for line in LINES:
        print(line[11:])                            # without the date, to fit the screen


asyncio.run(main())
