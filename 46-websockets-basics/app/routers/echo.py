# The smallest WebSocket: accept, then receive and send in a loop
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws/echo")
async def echo(websocket: WebSocket) -> None:
    await websocket.accept()                            # say yes to the upgrade
    try:
        while True:                                     # one connection, many messages
            text = await websocket.receive_text()       # waits - without blocking the server
            await websocket.send_text(f"echo: {text}")
    except WebSocketDisconnect as closed:               # the client closed the connection
        print(f"echo: client left (code {closed.code})")
