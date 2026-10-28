# Services = the business logic. No FastAPI, no HTTP here - just Python.
from app.schemas.course import CourseCreate, CourseOut

COURSES: dict[int, CourseOut] = {}       # our "database" for now


def list_courses(skip: int = 0, limit: int = 10) -> list[CourseOut]:
    return list(COURSES.values())[skip : skip + limit]


def get_course(course_id: int) -> CourseOut | None:
    return COURSES.get(course_id)


def create_course(data: CourseCreate) -> CourseOut:
    new_id = max(COURSES, default=0) + 1
    course = CourseOut(id=new_id, **data.model_dump())
    COURSES[new_id] = course
    return course


def delete_course(course_id: int) -> None:
    COURSES.pop(course_id, None)
