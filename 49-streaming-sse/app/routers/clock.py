# Homework 49: a clock over Server-Sent Events
import asyncio
from collections.abc import AsyncIterable
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.sse import EventSourceResponse, ServerSentEvent

router = APIRouter(tags=["Live"])


@router.get("/clock", response_class=EventSourceResponse)
async def clock(count: Annotated[int, Query(ge=1, le=60)] = 5,
                interval: Annotated[float, Query(ge=0, le=1)] = 1.0,
                ) -> AsyncIterable[ServerSentEvent]:
    """event: tick - the server time, once per second - then event: done"""
    for n in range(1, count + 1):
        await asyncio.sleep(interval)
        yield ServerSentEvent(event="tick", id=str(n),
                              data={"n": n, "time": datetime.now().strftime("%H:%M:%S")})
    yield ServerSentEvent(event="done", raw_data="[DONE]")
