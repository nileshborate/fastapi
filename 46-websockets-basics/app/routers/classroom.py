# A live classroom: everybody in it sees every message - and the teacher's announcements
from typing import Annotated

from fastapi import APIRouter, Path, WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError

from app.manager import manager
from app.schemas import Announcement, ChatIn, Delivered

router = APIRouter(tags=["Classroom"])

Name = Annotated[str, Path(min_length=2, max_length=20, pattern=r"^[A-Za-z]+$")]


@router.websocket("/ws/class/{name}")
async def classroom(websocket: WebSocket, name: Name) -> None:
    if name in manager.names:                            # homework 46: no two Ashas
        await websocket.accept()                         # accept first: the client sees why
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="name taken")
        return
    await manager.connect(websocket, name)
    await manager.broadcast({"type": "system", "text": f"{name} joined",
                             "online": manager.names})
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                message = ChatIn.model_validate_json(raw)   # bad JSON or bad fields -> error
            except ValidationError:
                await websocket.send_json({"type": "error",       # only to the sender
                                           "detail": 'send {"text": "1-500 characters"}'})
                continue
            if message.to:                               # homework 46: only to one student
                await send_private(websocket, name, message.to, message.text)
                continue
            await manager.broadcast({"type": "chat", "from": name, "text": message.text})
    except WebSocketDisconnect:
        left = manager.disconnect(websocket)
        await manager.broadcast({"type": "system", "text": f"{left} left",
                                 "online": manager.names})


async def send_private(websocket: WebSocket, sender: str, to: str, text: str) -> None:
    target = manager.find(to)
    if target is None:
        await websocket.send_json({"type": "error", "detail": f"{to} is not online"})
        return
    message = {"type": "private", "from": sender, "to": to, "text": text}
    await target.send_json(message)                       # only Ravi ...
    if target is not websocket:
        await websocket.send_json(message)                # ... and a copy for the sender


@router.post("/announcements", response_model=Delivered,
             status_code=status.HTTP_202_ACCEPTED)
async def announce(data: Announcement) -> Delivered:
    """a normal HTTP request - and every open WebSocket gets the message"""
    await manager.broadcast({"type": "announcement", "text": data.text})
    return Delivered(delivered_to=len(manager.active))


@router.get("/online")
async def online() -> dict[str, list[str]]:
    return {"online": manager.names}
