# Run: python -m demos.background
# BackgroundTasks: the client gets the answer FIRST - the slow work runs after it
import asyncio
import time

import httpx
import uvicorn
from fastapi import BackgroundTasks, FastAPI

app = FastAPI()
start = 0.0


def log(text: str) -> None:
    print(f"{time.perf_counter() - start:5.2f}s  {text}")


async def send_slow_email(to: str) -> None:      # FastAPI runs it AFTER the answer
    await asyncio.sleep(1.0)                     # pretend: talking to a mail server
    log(f"email sent to {to}")


@app.post("/register")
async def register(tasks: BackgroundTasks) -> dict[str, str]:
    tasks.add_task(send_slow_email, "asha@example.com")    # not run yet - only queued
    log("endpoint returns the answer")
    return {"status": "registered"}


async def main() -> None:
    global start
    server = uvicorn.Server(uvicorn.Config(app, port=8044, log_level="warning"))
    serving = asyncio.create_task(server.serve())          # a REAL server, in this process
    while not server.started:
        await asyncio.sleep(0.05)
    start = time.perf_counter()                          # the clock starts with the request
    async with httpx.AsyncClient() as client:
        response = await client.post("http://127.0.0.1:8044/register")
        log(f"client got {response.status_code} {response.json()}")
    await asyncio.sleep(1.5)                             # wait - the email comes later
    server.should_exit = True
    await serving


if __name__ == "__main__":
    asyncio.run(main())
