# Run: python -m demos.classroom
# Two students in the live class - the server PUSHES every message to both of them
import asyncio
import json

import httpx
from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import InvalidStatus

from app.main import app
from demos.common import HTTP, WS, log, serve


async def listen(name: str, websocket: ClientConnection) -> None:
    async for raw in websocket:                           # waits for the next push
        message = json.loads(raw)
        text = message.get("text") or message.get("detail")
        sender = message.get("from", message["type"])
        log(f"{name:<4} <- {sender}: {text}")


async def main() -> None:
    async with serve(app):
        asha = await connect(f"{WS}/ws/class/Asha")
        asha_task = asyncio.create_task(listen("asha", asha))
        await asyncio.sleep(0.2)
        ravi = await connect(f"{WS}/ws/class/Ravi")
        ravi_task = asyncio.create_task(listen("ravi", ravi))
        await asyncio.sleep(0.2)
        log("ravi -> {'text': 'Hello class!'}")
        await ravi.send(json.dumps({"text": "Hello class!"}))
        await asyncio.sleep(0.2)
        log("asha -> {'text': ''}   (too short)")
        await asha.send(json.dumps({"text": ""}))
        await asyncio.sleep(0.2)
        async with httpx.AsyncClient() as client:
            log("teacher: POST /announcements {'text': 'Quiz at 5 pm'}")
            response = await client.post(f"{HTTP}/announcements", json={"text": "Quiz at 5 pm"})
            log(f"teacher <- {response.status_code} {response.json()}")
            await asyncio.sleep(0.2)
            log("ravi closes the tab")
            await ravi.close()
            await asyncio.sleep(0.2)
            log(f"GET /online -> {(await client.get(f'{HTTP}/online')).json()}")
        await asha.close()
        await asyncio.gather(asha_task, ravi_task)
        try:
            await connect(f"{WS}/ws/class/A")              # a name with ONE letter
        except InvalidStatus as refused:
            log(f"name 'A' -> refused before accept: HTTP {refused.response.status_code}")


if __name__ == "__main__":
    asyncio.run(main())
