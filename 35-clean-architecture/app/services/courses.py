# Service layer: the business rules. No SQL, no HTTP - just the rules, in plain Python.
from app.config import get_settings
from app.errors import ConflictError, NotFoundError, RuleError
from app.models import Course, Teacher
from app.schemas import CourseCreate
from app.uow import UnitOfWork


class CourseService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow
        self.max_courses = get_settings().max_courses_per_teacher

    async def list(self) -> list[Course]:
        return await self.uow.courses.list()

    async def get(self, course_id: int) -> Course:
        course = await self.uow.courses.get(course_id)
        if course is None:
            raise NotFoundError("Course not found")
        return course

    async def create(self, data: CourseCreate) -> Course:
        teacher = await self._teacher_with_room(data.teacher_id)
        if await self.uow.courses.get_by_title(data.title) is not None:
            raise ConflictError("Course title already exists")
        course = Course(title=data.title, fee=data.fee, teacher=teacher)
        self.uow.courses.add(course)
        await self.uow.commit()
        return course

    async def transfer(self, course_id: int, teacher_id: int) -> Course:
        course = await self.get(course_id)
        if course.teacher.id == teacher_id:
            raise RuleError("The course already has this teacher")
        course.teacher = await self._teacher_with_room(teacher_id)
        await self.uow.commit()             # one commit for the whole change
        return course

    async def _teacher_with_room(self, teacher_id: int) -> Teacher:
        teacher = await self.uow.teachers.get(teacher_id)
        if teacher is None:
            raise NotFoundError("Teacher not found")
        if await self.uow.courses.count_for_teacher(teacher_id) >= self.max_courses:
            raise RuleError(f"A teacher can teach at most {self.max_courses} courses")
        return teacher

    # ------------------------------------------------------------ homework answer (Video 35)
    async def change_fee(self, course_id: int, fee: int) -> Course:
        course = await self.get(course_id)
        if fee > course.fee * 1.5:              # at most +50 % at once
            raise RuleError("A fee may go up at most 50% at once")
        course.fee = fee
        await self.uow.commit()
        return course
