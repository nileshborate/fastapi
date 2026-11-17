# ONE internal model and ONE store - every API version reads and writes the same data
from pydantic import BaseModel


class CourseRecord(BaseModel):              # how WE store a course (never sent as it is)
    id: int
    title: str
    teacher: str
    price_paise: int                        # money as an integer: 49900 paise = Rs 499.00
    currency: str = "INR"
    tags: list[str] = []


COURSES: dict[int, CourseRecord] = {
    1: CourseRecord(id=1, title="Python Basics", teacher="Nilesh", price_paise=49900,
                    tags=["python"]),
    2: CourseRecord(id=2, title="SQL Joins", teacher="Asha", price_paise=29950, tags=["sql"]),
    3: CourseRecord(id=3, title="FastAPI Mastery", teacher="Nilesh", price_paise=99900,
                    tags=["python", "api"]),
}


def get_course(course_id: int) -> CourseRecord | None:
    return COURSES.get(course_id)


def add_course(title: str, teacher: str, price_paise: int, tags: list[str]) -> CourseRecord:
    record = CourseRecord(id=max(COURSES, default=0) + 1, title=title, teacher=teacher,
                          price_paise=price_paise, tags=tags)
    COURSES[record.id] = record
    return record
