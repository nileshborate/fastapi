# The unit of work against a REAL database
import httpx
import pytest
from sqlalchemy import func, select

from app.errors import ConflictError
from app.models import Course, Teacher
from app.uow import UnitOfWork

pytestmark = pytest.mark.anyio


async def test_one_commit_for_both_repositories(api: httpx.AsyncClient) -> None:
    async with UnitOfWork() as uow:
        teacher = Teacher(name="Nilesh")
        uow.teachers.add(teacher)
        uow.courses.add(Course(title="FastAPI Basics", fee=299, teacher=teacher))
        await uow.commit()                  # both rows - one transaction
    async with UnitOfWork() as uow:
        assert len(await uow.courses.list()) == 1
        assert (await uow.teachers.list())[0].name == "Nilesh"


async def test_error_rolls_back_everything(api: httpx.AsyncClient) -> None:
    with pytest.raises(RuntimeError):
        async with UnitOfWork() as uow:
            uow.teachers.add(Teacher(name="Nilesh"))
            await uow.db.flush()            # the INSERT is sent ...
            raise RuntimeError("something failed")   # ... but never committed
    async with UnitOfWork() as uow:
        assert await uow.db.scalar(select(func.count()).select_from(Teacher)) == 0


async def test_integrity_error_becomes_conflict(api: httpx.AsyncClient) -> None:
    async with UnitOfWork() as uow:
        teacher = Teacher(name="Nilesh")
        for _ in range(2):                  # the service check skipped - like a race
            uow.courses.add(Course(title="FastAPI Basics", fee=299, teacher=teacher))
        with pytest.raises(ConflictError):
            await uow.commit()
