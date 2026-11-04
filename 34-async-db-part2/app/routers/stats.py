# asyncio.gather: four queries at the SAME time - each one with its OWN session
import asyncio

from fastapi import APIRouter
from sqlalchemy import func, select

from app.database import SessionLocal
from app.models import Course, Teacher
from app.schemas import Stats

router = APIRouter(prefix="/stats", tags=["Stats"])


async def count_teachers() -> int:
    async with SessionLocal() as db:            # its own session = its own connection
        return await db.scalar(select(func.count()).select_from(Teacher))


async def count_courses() -> int:
    async with SessionLocal() as db:
        return await db.scalar(select(func.count()).select_from(Course))


async def average_fee() -> float:
    async with SessionLocal() as db:
        avg = await db.scalar(select(func.avg(Course.fee)))
        return round(float(avg or 0), 2)        # PostgreSQL gives a Decimal, or None


async def top_courses(limit: int = 3) -> list[str]:
    async with SessionLocal() as db:
        stmt = select(Course.title).order_by(Course.fee.desc(), Course.title).limit(limit)
        return list((await db.scalars(stmt)).all())


@router.get("", response_model=Stats)
async def get_stats() -> Stats:
    # start all four, then wait for all four - the results come back in the SAME order
    teachers, courses, avg_fee, top = await asyncio.gather(
        count_teachers(), count_courses(), average_fee(), top_courses()
    )
    return Stats(teachers=teachers, courses=courses, average_fee=avg_fee, top_courses=top)
