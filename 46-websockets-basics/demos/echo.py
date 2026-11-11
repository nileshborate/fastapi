# Run: python -m demos.echo
# One HTTP request that UPGRADES - then one open connection for many messages
import asyncio

from websockets.asyncio.client import connect

from app.main import app
from demos.common import WS, log, serve


async def main() -> None:
    async with serve(app), connect(f"{WS}/ws/echo") as websocket:
        handshake = websocket.response                    # the HTTP answer to our upgrade
        log(f"handshake: {handshake.status_code} {handshake.reason_phrase}")
        log(f"  Upgrade: {handshake.headers['Upgrade']}  "
            f"Connection: {handshake.headers['Connection']}")
        for text in ("hello", "how are you?", "bye"):
            await websocket.send(text)
            log(f"sent      {text!r}")
            log(f"received  {await websocket.recv()!r}")
    log("closed")


if __name__ == "__main__":
    asyncio.run(main())
