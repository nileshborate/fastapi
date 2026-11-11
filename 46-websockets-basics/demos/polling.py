# Run: python -m demos.polling
# Before WebSockets: the client ASKS again and again. One new message, how many requests?
import asyncio

import httpx
from fastapi import FastAPI

from demos.common import HTTP, log, serve

app = FastAPI()
messages: list[str] = []
arrived = [0.0]


@app.get("/messages")
async def get_messages(after: int = 0) -> list[str]:
    return messages[after:]


async def teacher() -> None:
    await asyncio.sleep(2.3)
    messages.append("Quiz at 5 pm")                       # the ONLY new message
    arrived[0] = asyncio.get_running_loop().time()
    log("server: a new message arrives")


async def main() -> None:
    async with serve(app), httpx.AsyncClient() as client:
        asyncio.create_task(teacher())
        requests, late = 0, 0.0
        for _ in range(6):                                # every 0.5 s: anything new?
            requests += 1
            news = (await client.get(f"{HTTP}/messages")).json()
            log(f"client: GET /messages -> {news}")
            if news:
                late = asyncio.get_running_loop().time() - arrived[0]
            await asyncio.sleep(0.5)
        log(f"{requests} requests - only 1 brought news, and it came {late:.2f} s late")


if __name__ == "__main__":
    asyncio.run(main())
