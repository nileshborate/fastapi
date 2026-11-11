# Chat rooms: one room per course - only enrolled users get in, with a valid token
import asyncio
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, WebSocket, WebSocketDisconnect, status
from fastapi.exceptions import WebSocketException
from pydantic import ValidationError

from app.deps import CurrentUser, Session, Teacher, seconds_left
from app.rooms import rooms
from app.schemas import Announcement, ChatIn, Delivered

router = APIRouter(tags=["Rooms"])

Room = Annotated[str, Path(min_length=2, max_length=20, pattern=r"^[a-z]+$")]
POLICY = status.WS_1008_POLICY_VIOLATION


@router.websocket("/ws/rooms/{room}")
async def room_chat(websocket: WebSocket, room: Room, session: Session) -> None:
    user = session.user
    if room not in user.rooms:                             # authorization - still before accept
        raise WebSocketException(code=POLICY, reason="not enrolled in this room")
    await websocket.accept()
    if history := rooms.recent(room):                      # homework 47: what you missed
        await websocket.send_json({"type": "history", "room": room, "messages": history})
    rooms.join(room, websocket, user.username)
    await rooms.broadcast(room, {"type": "system", "room": room,
                                 "text": f"{user.username} joined",
                                 "members": rooms.members(room)})
    try:
        while True:
            # wait for a message - but never longer than the token lives
            raw = await asyncio.wait_for(websocket.receive_text(),
                                         timeout=seconds_left(session))
            try:
                message = ChatIn.model_validate_json(raw)
            except ValidationError:
                await websocket.send_json({"type": "error", "detail": 'send {"text": "..."}'})
                continue
            chat = {"type": "chat", "room": room, "from": user.username, "text": message.text}
            rooms.remember(room, chat)
            await rooms.broadcast(room, chat)
    except TimeoutError:                                   # the token expired: log in again
        await websocket.close(code=POLICY, reason="token expired")
    except WebSocketDisconnect:
        pass                                               # the user closed the tab
    finally:                                               # in EVERY case: leave the room
        rooms.leave(room, websocket)
        await rooms.broadcast(room, {"type": "system", "room": room,
                                     "text": f"{user.username} left",
                                     "members": rooms.members(room)})


@router.get("/rooms/{room}/members")
async def members(room: Room, user: CurrentUser) -> dict[str, str | list[str]]:
    if room not in user.rooms:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Room not found")
    return {"room": room, "members": rooms.members(room)}


@router.post("/rooms/{room}/announcements", response_model=Delivered,
             status_code=status.HTTP_202_ACCEPTED)
async def announce(room: Room, data: Announcement, teacher: Teacher) -> Delivered:
    announcement = {"type": "announcement", "room": room, "from": teacher.username,
                    "text": data.text}
    rooms.remember(room, announcement)
    await rooms.broadcast(room, announcement)
    return Delivered(room=room, delivered_to=rooms.count(room))


@router.delete("/rooms/{room}/members/{username}")
async def remove_member(room: Room, username: str, teacher: Teacher) -> dict[str, str | int]:
    """homework 47: close every connection of this user in this room"""
    connections = rooms.connections_of(room, username)
    if not connections:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not in this room")
    for websocket in connections:
        await websocket.close(code=POLICY, reason="removed by teacher")
    return {"room": room, "removed": username, "connections": len(connections)}
