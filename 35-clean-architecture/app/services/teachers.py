from app.errors import NotFoundError, RuleError
from app.models import Teacher
from app.schemas import TeacherCreate
from app.uow import UnitOfWork


class TeacherService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def list(self) -> list[Teacher]:
        return await self.uow.teachers.list()

    async def create(self, data: TeacherCreate) -> Teacher:
        teacher = Teacher(name=data.name)
        self.uow.teachers.add(teacher)
        await self.uow.commit()
        return teacher

    # ------------------------------------------------------------ homework answer (Video 35)
    async def delete(self, teacher_id: int) -> None:
        teacher = await self.uow.teachers.get(teacher_id)
        if teacher is None:
            raise NotFoundError("Teacher not found")
        if await self.uow.courses.count_for_teacher(teacher_id) > 0:
            raise RuleError("The teacher still has courses")
        await self.uow.teachers.delete(teacher)
        await self.uow.commit()
