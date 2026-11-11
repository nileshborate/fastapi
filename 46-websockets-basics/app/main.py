# Video 46 - WebSockets Part 1: real-time basics, accept / send / receive, a connection manager
# fastapi dev app/main.py   ->   http://localhost:8000  (open it in two browser windows)
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.routers import classroom, echo

PAGE = (Path(__file__).parent / "static" / "classroom.html").read_text()

app = FastAPI(title="Course Hub Live", version="1.0.0")
app.include_router(echo.router)
app.include_router(classroom.router)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def page() -> str:
    return PAGE                                         # a tiny browser client for the demo
