from fastapi import APIRouter, status

from app.dependencies import CourseDep, DBSession, Pagination
from app.models import Course
from app.schemas.course import CourseCreate, CourseOut
from app.services import course_service

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("", response_model=list[CourseOut])
def list_courses(db: DBSession, page: Pagination) -> list[Course]:
    return course_service.list_courses(db, page.skip, page.limit)


@router.get("/{course_id}", response_model=CourseOut)
def get_course(course: CourseDep) -> Course:
    return course


@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(data: CourseCreate, db: DBSession) -> Course:
    return course_service.create_course(db, data)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course: CourseDep, db: DBSession) -> None:
    course_service.delete_course(db, course)
