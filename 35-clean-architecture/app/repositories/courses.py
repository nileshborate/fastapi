# Repository: ALL the SQL for courses - the rest of the app never writes select(...)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Course

WITH_TEACHER = selectinload(Course.teacher)


class CourseRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, course_id: int) -> Course | None:
        return await self.db.get(Course, course_id, options=[WITH_TEACHER])

    async def get_by_title(self, title: str) -> Course | None:
        return await self.db.scalar(select(Course).where(Course.title == title))

    async def list(self) -> list[Course]:
        stmt = select(Course).options(WITH_TEACHER).order_by(Course.id)
        return list((await self.db.scalars(stmt)).all())

    async def count_for_teacher(self, teacher_id: int) -> int:
        stmt = select(func.count()).select_from(Course).where(Course.teacher_id == teacher_id)
        return await self.db.scalar(stmt)

    def add(self, course: Course) -> None:
        self.db.add(course)                 # no commit here - the unit of work decides
