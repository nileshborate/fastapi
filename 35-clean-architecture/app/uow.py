# Unit of Work: ONE session, all repositories on it, ONE commit - or a rollback
from collections.abc import AsyncIterator
from types import TracebackType

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database import SessionLocal
from app.errors import ConflictError
from app.repositories import CourseRepository, TeacherRepository


class UnitOfWork:
    def __init__(self, factory: async_sessionmaker[AsyncSession] = SessionLocal) -> None:
        self.factory = factory

    async def __aenter__(self) -> "UnitOfWork":
        self.db = self.factory()
        self.courses = CourseRepository(self.db)        # both repositories -
        self.teachers = TeacherRepository(self.db)      # the SAME session
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None,
                        exc: BaseException | None, tb: TracebackType | None) -> None:
        if exc_type is not None:
            await self.db.rollback()        # something failed: undo everything
        await self.db.close()

    async def commit(self) -> None:
        try:
            await self.db.commit()
        except IntegrityError:              # e.g. two requests, the same title, at once
            await self.db.rollback()
            raise ConflictError("The data conflicts with existing data") from None

    async def rollback(self) -> None:
        await self.db.rollback()


async def get_uow() -> AsyncIterator[UnitOfWork]:
    async with UnitOfWork() as uow:         # one unit of work per request
        yield uow
