from fastapi import APIRouter, status

from app.dependencies import DBSession
from app.models import Course
from app.schemas.course import CourseCreate, CourseOut
from app.schemas.enrollment import CourseDetail, Status
from app.services import course_service

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("", response_model=list[CourseOut])
def list_courses(db: DBSession) -> list[Course]:
    return course_service.list_courses(db)


@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(data: CourseCreate, db: DBSession) -> Course:
    return course_service.create_course(db, data)


@router.get("/{course_id}", response_model=CourseDetail)                # + the roster (student, enrolled_at, grade)
def get_course(course_id: int, db: DBSession, status: Status | None = None) -> Course:
    return course_service.get_course_detail(db, course_id, status)     # ?status=active (homework)
