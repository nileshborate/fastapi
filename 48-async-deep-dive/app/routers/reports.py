# Homework 48: a legacy (blocking) report - called from async def without freezing the server
from typing import Annotated

from fastapi import APIRouter, Path
from fastapi.concurrency import run_in_threadpool

from app.work import slow_report

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/{n}")
async def report(n: Annotated[int, Path(ge=1, le=1000)]) -> dict[str, int | str]:
    text = await run_in_threadpool(slow_report, 1.0)       # the function + its argument
    return {"report": n, "status": text}
