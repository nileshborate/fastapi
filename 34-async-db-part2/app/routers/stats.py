# asyncio.gather: four queries at the SAME time - each one with its OWN session
import asyncio

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.database import SessionLocal
from app.models import Course, Teacher
from app.schemas import Stats, TeacherSummary

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


# ---------------------------------------------------------------- homework answer (Video 34)
async def teacher_name(teacher_id: int) -> str | None:
    async with SessionLocal() as db:
        return await db.scalar(select(Teacher.name).where(Teacher.id == teacher_id))


async def teacher_course_count(teacher_id: int) -> int:
    async with SessionLocal() as db:
        stmt = select(func.count()).select_from(Course).where(Course.teacher_id == teacher_id)
        return await db.scalar(stmt)


async def teacher_total_fees(teacher_id: int) -> int:
    async with SessionLocal() as db:
        total = func.coalesce(func.sum(Course.fee), 0)        # no courses: SUM is NULL -> 0
        stmt = select(total).where(Course.teacher_id == teacher_id)
        return int(await db.scalar(stmt))     # PostgreSQL's SUM gives a bigint - int() is safe


teachers_router = APIRouter(prefix="/teachers", tags=["Stats"])


@teachers_router.get("/{teacher_id}/summary", response_model=TeacherSummary)
async def teacher_summary(teacher_id: int) -> TeacherSummary:
    name, count, total = await asyncio.gather(          # three queries, three sessions
        teacher_name(teacher_id),
        teacher_course_count(teacher_id),
        teacher_total_fees(teacher_id),
    )
    if name is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    return TeacherSummary(id=teacher_id, name=name, courses=count, total_fees=total)
