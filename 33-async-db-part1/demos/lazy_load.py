# The async trap: lazy loading. Run:  python -m demos.lazy_load
import asyncio
import os
import warnings

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./demo.db")   # a throw-away database
# the failed lazy load leaves an un-awaited coroutine behind - hide that warning in the demo
warnings.filterwarnings("ignore", message="coroutine .* was never awaited")

from sqlalchemy import select  # noqa: E402
from sqlalchemy.exc import MissingGreenlet, StatementError  # noqa: E402
from sqlalchemy.orm import selectinload  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Course, Teacher  # noqa: E402


async def main() -> None:
    async with engine.begin() as conn:                  # a demo table set (NOT for the app)
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as db:
        db.add(Course(title="FastAPI Basics", fee=299, teacher=Teacher(name="Nilesh")))
        await db.commit()

    # 1. lazy loading: course.teacher is NOT loaded - SQLAlchemy would need a new query ...
    async with SessionLocal() as db:
        course = await db.scalar(select(Course))
        try:
            print(course.teacher.name)
        except (StatementError, MissingGreenlet) as exc:  # ... and async may not do that
            error = getattr(exc, "orig", exc)           # aiosqlite wraps it, asyncpg doesn't
            print("1. lazy:        ", type(error).__name__, "-", str(error).split(";")[0])

    # 2. load it in the SAME await: selectinload
    async with SessionLocal() as db:
        course = await db.scalar(select(Course).options(selectinload(Course.teacher)))
        print("2. selectinload:", course.title, "by", course.teacher.name)

    # 3. or load it later - with an await
    async with SessionLocal() as db:
        course = await db.scalar(select(Course))
        teacher = await course.awaitable_attrs.teacher
        print("3. awaitable:   ", course.title, "by", teacher.name)

    await engine.dispose()
    os.remove("demo.db")


asyncio.run(main())
