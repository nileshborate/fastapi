# Homework answer (Video 35): the two new rules - with the fakes (no database) + one API test
import httpx
import pytest

from app.errors import NotFoundError, RuleError
from app.models import Teacher
from app.schemas import CourseCreate
from app.services.courses import CourseService
from app.services.teachers import TeacherService
from tests.fakes import FakeUnitOfWork

pytestmark = pytest.mark.anyio


@pytest.fixture
def uow() -> FakeUnitOfWork:
    fake = FakeUnitOfWork()
    fake.teachers.add(Teacher(name="Nilesh"))
    fake.teachers.add(Teacher(name="Asha"))
    return fake


async def test_fee_may_go_up_50_percent(uow: FakeUnitOfWork) -> None:
    service = CourseService(uow)
    await service.create(CourseCreate(title="FastAPI Basics", fee=200, teacher_id=1))
    assert (await service.change_fee(1, 300)).fee == 300        # +50 %: allowed
    with pytest.raises(RuleError, match="at most 50%"):
        await service.change_fee(1, 451)                        # 300 * 1.5 = 450
    assert (await service.change_fee(1, 100)).fee == 100        # down: always allowed
    with pytest.raises(NotFoundError):
        await service.change_fee(9, 100)


async def test_delete_teacher_only_without_courses(uow: FakeUnitOfWork) -> None:
    await CourseService(uow).create(CourseCreate(title="FastAPI Basics", fee=1, teacher_id=1))
    service = TeacherService(uow)
    with pytest.raises(RuleError, match="still has courses"):
        await service.delete(1)
    await service.delete(2)                                     # Asha: no courses
    assert await uow.teachers.get(2) is None
    with pytest.raises(NotFoundError):
        await service.delete(9)


async def test_api(api: httpx.AsyncClient) -> None:
    await api.post("/teachers", json={"name": "Nilesh"})
    body = {"title": "FastAPI Basics", "fee": 200, "teacher_id": 1}
    await api.post("/courses", json=body)
    assert (await api.patch("/courses/1/fee", json={"fee": 300})).json()["fee"] == 300
    assert (await api.patch("/courses/1/fee", json={"fee": 999})).status_code == 422
    assert (await api.delete("/teachers/1")).status_code == 422
    await api.post("/teachers", json={"name": "Asha"})
    assert (await api.delete("/teachers/2")).status_code == 204
