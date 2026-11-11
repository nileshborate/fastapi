# A fake, SLOW database - every query takes db_delay seconds, and we count the queries
import asyncio

from pydantic import BaseModel

from app.config import get_settings


class Course(BaseModel):
    id: int
    title: str
    teacher: str
    price: int
    students: int


COURSES: dict[int, Course] = {
    1: Course(id=1, title="Python Basics", teacher="Nilesh", price=499, students=1200),
    2: Course(id=2, title="SQL Joins", teacher="Asha", price=299, students=800),
    3: Course(id=3, title="FastAPI Mastery", teacher="Nilesh", price=999, students=2500),
    4: Course(id=4, title="Docker 101", teacher="Ravi", price=399, students=650),
}
queries = {"count": 0}                    # how many times did we really ask the database?


async def fetch_course(course_id: int) -> Course | None:
    queries["count"] += 1
    await asyncio.sleep(get_settings().db_delay)          # the network + the query
    return COURSES.get(course_id)


async def save_course(course: Course) -> None:
    queries["count"] += 1
    await asyncio.sleep(get_settings().db_delay)
    COURSES[course.id] = course


async def popular_stats() -> dict[str, int | str]:
    """an expensive report: it reads every course"""
    queries["count"] += 1
    await asyncio.sleep(get_settings().db_delay * 3)
    top = max(COURSES.values(), key=lambda c: c.students)
    return {"courses": len(COURSES), "students": sum(c.students for c in COURSES.values()),
            "top_course": top.title}
