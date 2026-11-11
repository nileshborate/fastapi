# A RoomManager: one group of connections PER ROOM - a message only reaches its own room
from fastapi import WebSocket, WebSocketDisconnect


class RoomManager:
    def __init__(self) -> None:
        self.rooms: dict[str, dict[WebSocket, str]] = {}      # room -> {connection: username}

    def join(self, room: str, websocket: WebSocket, username: str) -> None:
        self.rooms.setdefault(room, {})[websocket] = username   # a new room is created here

    def leave(self, room: str, websocket: WebSocket) -> None:
        members = self.rooms.get(room, {})
        members.pop(websocket, None)
        if not members:
            self.rooms.pop(room, None)                          # an empty room disappears

    def members(self, room: str) -> list[str]:
        return sorted(set(self.rooms.get(room, {}).values()))  # two tabs = one member

    def count(self, room: str) -> int:
        return len(self.rooms.get(room, {}))

    async def broadcast(self, room: str, message: dict) -> None:
        for websocket in list(self.rooms.get(room, {})):       # ONLY this room's connections
            try:
                await websocket.send_json(message)
            except (WebSocketDisconnect, RuntimeError):
                self.leave(room, websocket)


rooms = RoomManager()            # still one process - Redis pub/sub later in the course
