# A REAL server for the demos (uvicorn in a thread, port 8055) + every log line it writes
import asyncio
import logging
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import uvicorn

from app.main import app

PORT = 8055
LINES: list[str] = []                       # what the server wrote, one line per record


class Capture(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        if record.name.startswith("app"):           # only OUR app's lines
            LINES.append(self.format(record))


def _capture() -> None:
    console = logging.getLogger().handlers[0]
    keep = Capture()
    keep.setFormatter(console.formatter)            # the same format as the console
    for f in console.filters:
        keep.addFilter(f)
    console.setLevel(logging.CRITICAL)              # quiet - the demo prints what it needs
    logging.getLogger().addHandler(keep)


@asynccontextmanager
async def serve() -> AsyncIterator[httpx.AsyncClient]:
    _capture()
    config = uvicorn.Config(app, port=PORT, log_config=None)     # keep OUR logging setup
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        await asyncio.sleep(0.05)
    LINES.clear()                                   # drop the startup lines
    try:
        async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{PORT}", timeout=30) as client:
            yield client
    finally:
        server.should_exit = True
        thread.join()
