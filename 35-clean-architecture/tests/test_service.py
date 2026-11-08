# Unit tests: the business rules with FAKES - no database, no HTTP, milliseconds
import pytest

from app.errors import ConflictError, NotFoundError, RuleError
from app.models import Teacher
from app.schemas import CourseCreate
from app.services.courses import CourseService
from tests.fakes import FakeUnitOfWork

pytestmark = pytest.mark.anyio


@pytest.fixture
def uow() -> FakeUnitOfWork:
    fake = FakeUnitOfWork()
    fake.teachers.add(Teacher(name="Nilesh"))
    fake.teachers.add(Teacher(name="Asha"))
    return fake


def course(title: str, teacher_id: int = 1) -> CourseCreate:
    return CourseCreate(title=title, fee=299, teacher_id=teacher_id)


async def test_create_saves_once(uow: FakeUnitOfWork) -> None:
    created = await CourseService(uow).create(course("FastAPI Basics"))
    assert created.id == 1 and created.teacher.name == "Nilesh"
    assert uow.commits == 1


async def test_unknown_teacher(uow: FakeUnitOfWork) -> None:
    with pytest.raises(NotFoundError, match="Teacher not found"):
        await CourseService(uow).create(course("FastAPI Basics", teacher_id=9))
    assert uow.commits == 0                 # nothing saved


async def test_duplicate_title(uow: FakeUnitOfWork) -> None:
    service = CourseService(uow)
    await service.create(course("FastAPI Basics"))
    with pytest.raises(ConflictError):
        await service.create(course("FastAPI Basics", teacher_id=2))


async def test_max_three_courses(uow: FakeUnitOfWork) -> None:
    service = CourseService(uow)
    for title in ("Course A", "Course B", "Course C"):
        await service.create(course(title))
    with pytest.raises(RuleError, match="at most 3 courses"):
        await service.create(course("Course D"))
    assert uow.commits == 3


async def test_transfer(uow: FakeUnitOfWork) -> None:
    service = CourseService(uow)
    await service.create(course("FastAPI Basics"))
    moved = await service.transfer(1, teacher_id=2)
    assert moved.teacher.name == "Asha" and uow.commits == 2
    with pytest.raises(RuleError, match="already has this teacher"):
        await service.transfer(1, teacher_id=2)
