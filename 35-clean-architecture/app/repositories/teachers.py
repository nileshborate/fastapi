# Repository: ALL the SQL for one model - and nothing else (no HTTP, no rules, no commit)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Teacher


class TeacherRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, teacher_id: int) -> Teacher | None:
        return await self.db.get(Teacher, teacher_id)

    async def list(self) -> list[Teacher]:
        return list((await self.db.scalars(select(Teacher).order_by(Teacher.id))).all())

    def add(self, teacher: Teacher) -> None:
        self.db.add(teacher)

    async def delete(self, teacher: Teacher) -> None:      # homework (Video 35)
        await self.db.delete(teacher)
