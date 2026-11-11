# A ConnectionManager: who is connected RIGHT NOW - and how to reach all of them
from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self) -> None:
        self.active: dict[WebSocket, str] = {}          # open connection -> student name

    async def connect(self, websocket: WebSocket, name: str) -> None:
        await websocket.accept()                        # the handshake: 101 Switching Protocols
        self.active[websocket] = name

    def disconnect(self, websocket: WebSocket) -> str:
        return self.active.pop(websocket)               # the name of the one who left

    @property
    def names(self) -> list[str]:
        return sorted(self.active.values())

    async def broadcast(self, message: dict) -> None:
        for websocket in list(self.active):             # a copy: the dict may change
            try:
                await websocket.send_json(message)
            except (WebSocketDisconnect, RuntimeError):  # gone in the meantime: forget it
                self.active.pop(websocket, None)


manager = ConnectionManager()      # ONE per process - several workers need Redis (Part 2)
