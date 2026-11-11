# Live data over plain HTTP: JSON Lines and Server-Sent Events (FastAPI 0.135+)
import asyncio
from collections.abc import AsyncIterable
from typing import Annotated

from fastapi import APIRouter, Header, Path, Query
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel, Field

from app.data import Lesson, slow_lessons

router = APIRouter(tags=["Live"])

STEPS = 5
cleanups: list[str] = []                  # the demo + tests look here: did the stream stop?


@router.get("/lessons/stream")
async def stream_lessons(count: Annotated[int, Query(ge=1, le=100)] = 5,
                         delay: Annotated[float, Query(ge=0, le=2)] = 0.3,
                         ) -> AsyncIterable[Lesson]:
    """yield + no response_class = JSON Lines: one JSON object per line"""
    async for lesson in slow_lessons(count, delay):
        yield lesson


@router.get("/jobs/{job}/progress", response_class=EventSourceResponse)
async def job_progress(job: Annotated[str, Path(pattern=r"^[a-z0-9-]{1,20}$")],
                       last_event_id: Annotated[int | None, Header()] = None,
                       delay: Annotated[float, Query(ge=0, le=2)] = 0.5,
                       ) -> AsyncIterable[ServerSentEvent]:
    """Server-Sent Events: progress of a long job, step by step"""
    start = last_event_id + 1 if last_event_id is not None else 1   # resume after a drop
    step = start - 1
    try:
        for step in range(start, STEPS + 1):
            await asyncio.sleep(delay)                                # the "work"
            yield ServerSentEvent(event="progress", id=str(step), retry=3000,
                                  data={"job": job, "step": step, "of": STEPS,
                                        "percent": step * 100 // STEPS})
        yield ServerSentEvent(event="done", raw_data="[DONE]")
    finally:
        cleanups.append(f"{job}: stopped after step {step}")  # runs even if the client leaves


class Prompt(BaseModel):
    text: str = Field(min_length=1, max_length=200)


@router.post("/chat/stream", response_class=EventSourceResponse)
async def chat_stream(prompt: Prompt) -> AsyncIterable[ServerSentEvent]:
    """like an AI chat: the answer arrives word by word - over POST"""
    answer = f"You asked: {prompt.text} - streaming sends each word as soon as it is ready."
    for word in answer.split():
        await asyncio.sleep(0.05)
        yield ServerSentEvent(event="token", data=word)
    yield ServerSentEvent(event="done", raw_data="[DONE]")
