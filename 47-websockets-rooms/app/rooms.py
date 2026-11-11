# A RoomManager: one group of connections PER ROOM - a message only reaches its own room
from collections import deque

from fastapi import WebSocket, WebSocketDisconnect

HISTORY = 20                                                    # homework 47


class RoomManager:
    def __init__(self) -> None:
        self.rooms: dict[str, dict[WebSocket, str]] = {}      # room -> {connection: username}
        self.history: dict[str, deque[dict]] = {}             # room -> the last 20 messages

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

    def remember(self, room: str, message: dict) -> None:       # homework 47
        self.history.setdefault(room, deque(maxlen=HISTORY)).append(message)

    def recent(self, room: str) -> list[dict]:
        return list(self.history.get(room, []))

    def connections_of(self, room: str, username: str) -> list[WebSocket]:
        return [ws for ws, name in self.rooms.get(room, {}).items() if name == username]

    async def broadcast(self, room: str, message: dict) -> None:
        for websocket in list(self.rooms.get(room, {})):       # ONLY this room's connections
            try:
                await websocket.send_json(message)
            except (WebSocketDisconnect, RuntimeError):
                self.leave(room, websocket)


rooms = RoomManager()            # still one process - Redis pub/sub later in the course
