# Video 47 - WebSockets Part 2: chat rooms, broadcasting to a room, auth over WebSockets
from fastapi import FastAPI

from app.routers import auth, rooms

app = FastAPI(title="Course Hub Rooms", version="1.0.0")
app.include_router(auth.router)
app.include_router(rooms.router)
