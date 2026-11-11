# Run: python -m demos.auth
# The token travels as ?token=... - checked BEFORE accept, and again when it expires
import asyncio
from datetime import timedelta

from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed, InvalidStatus

from app.security import create_access_token
from demos.common import WS, log, login, serve


async def try_join(label: str, url: str) -> None:
    try:
        async with connect(url) as websocket:
            log(f"{label:<28} -> 101, then: {await websocket.recv()}")
    except InvalidStatus as refused:
        log(f"{label:<28} -> refused: HTTP {refused.response.status_code}")


async def main() -> None:
    async with serve() as client:
        ravi = await login(client, "ravi")
        await try_join("no token", f"{WS}/ws/rooms/python")
        await try_join("token=garbage", f"{WS}/ws/rooms/python?token=garbage")
        await try_join("ravi -> sql (not enrolled)", f"{WS}/ws/rooms/sql?token={ravi}")
        await try_join("ravi -> python", f"{WS}/ws/rooms/python?token={ravi}")

        short = create_access_token("asha", timedelta(seconds=3))   # lives 3 seconds
        async with connect(f"{WS}/ws/rooms/python?token={short}") as websocket:
            log(f"asha (3-second token) -> {await websocket.recv()}")
            try:
                await websocket.recv()                              # just wait ...
            except ConnectionClosed as closed:
                log(f"server closed: code {closed.rcvd.code}, reason {closed.rcvd.reason!r}")


if __name__ == "__main__":
    asyncio.run(main())
