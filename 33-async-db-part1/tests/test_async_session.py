# AsyncSession directly - an async test function (pytest + anyio)
import pytest
from sqlalchemy import select
from sqlalchemy.exc import MissingGreenlet, StatementError
from sqlalchemy.orm import selectinload

from app.database import SessionLocal, engine
from app.models import Course, Teacher

pytestmark = [
    pytest.mark.anyio,
    # the failed lazy load leaves an un-awaited coroutine behind - expected here
    pytest.mark.filterwarnings("ignore:coroutine .* was never awaited:RuntimeWarning"),
]


@pytest.fixture
async def course_in_db(client) -> None:  # noqa: ANN001 - client: the database is built
    async with SessionLocal() as db:
        db.add(Course(title="FastAPI Basics", fee=299, teacher=Teacher(name="Nilesh")))
        await db.commit()
    yield
    await engine.dispose()                  # connections of THIS event loop


async def test_lazy_loading_fails_in_async(course_in_db: None) -> None:
    async with SessionLocal() as db:
        course = await db.scalar(select(Course))
        # aiosqlite wraps it in a StatementError, asyncpg raises MissingGreenlet itself
        with pytest.raises((StatementError, MissingGreenlet), match="greenlet_spawn"):
            course.teacher                  # a hidden query - not allowed without await
        await db.rollback()                 # clean up the failed attempt


async def test_selectinload_loads_it_in_the_same_await(course_in_db: None) -> None:
    async with SessionLocal() as db:
        course = await db.scalar(select(Course).options(selectinload(Course.teacher)))
        assert course.teacher.name == "Nilesh"


async def test_awaitable_attrs(course_in_db: None) -> None:
    async with SessionLocal() as db:
        course = await db.scalar(select(Course))
        teacher = await course.awaitable_attrs.teacher
        assert teacher.name == "Nilesh"
