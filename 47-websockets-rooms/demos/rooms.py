# Run: python -m demos.rooms
# Two rooms - python and sql. A message only reaches its own room.
import asyncio
import json

from websockets.asyncio.client import ClientConnection, connect

from demos.common import HTTP, WS, log, login, serve


async def listen(label: str, websocket: ClientConnection) -> None:
    async for raw in websocket:
        m = json.loads(raw)
        sender = f"{m['from']}: " if "from" in m else ""
        log(f"{label:<9} <- {m['type']:<12} {sender}{m['text']}")


async def main() -> None:
    async with serve() as client:
        names = ("asha", "ravi", "meera", "nilesh")
        tokens = {name: await login(client, name) for name in names}
        sockets, tasks = {}, []
        for label, name, room in [("asha@py", "asha", "python"), ("asha@sql", "asha", "sql"),
                                  ("ravi@py", "ravi", "python"), ("meera@sql", "meera", "sql")]:
            sockets[label] = await connect(f"{WS}/ws/rooms/{room}?token={tokens[name]}")
            tasks.append(asyncio.create_task(listen(label, sockets[label])))
            await asyncio.sleep(0.15)
        log("---- asha writes in python")
        await sockets["asha@py"].send(json.dumps({"text": "Python quiz tomorrow?"}))
        await asyncio.sleep(0.2)
        log("---- meera writes in sql")
        await sockets["meera@sql"].send(json.dumps({"text": "Who has the SQL notes?"}))
        await asyncio.sleep(0.2)
        log("---- the teacher: POST /rooms/python/announcements")
        response = await client.post(f"{HTTP}/rooms/python/announcements",
                                     json={"text": "Quiz at 5 pm"},
                                     headers={"Authorization": f"Bearer {tokens['nilesh']}"})
        await asyncio.sleep(0.2)
        log(f"teacher   <- {response.status_code} {response.json()}")
        log("---- asha closes her python tab")
        await sockets["asha@py"].close()
        await asyncio.sleep(0.2)
        for task in tasks:
            task.cancel()                                  # the end of the demo


if __name__ == "__main__":
    asyncio.run(main())
