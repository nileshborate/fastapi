# In-memory fakes: the SAME methods as the real repositories and unit of work - no database
from app.models import Course, Teacher


class FakeTeacherRepository:
    def __init__(self) -> None:
        self.items: dict[int, Teacher] = {}

    async def get(self, teacher_id: int) -> Teacher | None:
        return self.items.get(teacher_id)

    async def list(self) -> list[Teacher]:
        return list(self.items.values())

    def add(self, teacher: Teacher) -> None:
        teacher.id = len(self.items) + 1
        self.items[teacher.id] = teacher

    async def delete(self, teacher: Teacher) -> None:      # homework (Video 35)
        del self.items[teacher.id]


class FakeCourseRepository:
    def __init__(self) -> None:
        self.items: dict[int, Course] = {}

    async def get(self, course_id: int) -> Course | None:
        return self.items.get(course_id)

    async def get_by_title(self, title: str) -> Course | None:
        return next((c for c in self.items.values() if c.title == title), None)

    async def list(self) -> list[Course]:
        return list(self.items.values())

    async def count_for_teacher(self, teacher_id: int) -> int:
        return sum(1 for c in self.items.values() if c.teacher.id == teacher_id)

    def add(self, course: Course) -> None:
        course.id = len(self.items) + 1
        self.items[course.id] = course


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.teachers = FakeTeacherRepository()
        self.courses = FakeCourseRepository()
        self.commits = 0                    # so a test can check: was it saved?

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        pass
