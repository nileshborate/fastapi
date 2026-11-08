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
