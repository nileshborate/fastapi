# Video 49 - Streaming responses and Server-Sent Events
# fastapi dev app/main.py   ->   http://localhost:8000  (a live progress bar)
import tempfile
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.data import csv_rows
from app.routers import files, live

PAGE = (Path(__file__).parent / "static" / "live.html").read_text()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    with tempfile.TemporaryDirectory() as folder:          # a "report" that exists on disk
        path = Path(folder) / "report.csv"
        with path.open("w") as file:
            file.writelines(csv_rows(50_000))
        app.state.report_path = path
        yield


app = FastAPI(title="Course Hub Streams", version="1.0.0", lifespan=lifespan)
app.include_router(files.router)
app.include_router(live.router)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def page() -> str:
    return PAGE
