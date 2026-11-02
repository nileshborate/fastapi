# Routers = the HTTP layer. Shared logic comes from dependencies.
from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.dependencies import (
    CourseDep, DBSession, Filters, Pagination, SettingsDep,
    allow_staff, require_admin, verify_api_key,
)
from app.models import Course
from app.schemas.course import CourseCreate, CourseOut
from app.services import course_service
from app.tasks import write_log

router = APIRouter(prefix="/courses", tags=["Courses"])


# The functions return database objects (Course).  response_model = the shape the client gets.
@router.get("", response_model=list[CourseOut])
def list_courses(db: DBSession, page: Pagination, filters: Filters) -> list[Course]:
    return course_service.list_courses(db, page.skip, page.limit, filters.min_price, filters.max_price)


@router.get("/{course_id}", response_model=CourseOut)
def get_course(course: CourseDep) -> Course:
    return course


@router.post(
    "",
    response_model=CourseOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_api_key), Depends(allow_staff)],
)
def create_course(
    data: CourseCreate, db: DBSession, background_tasks: BackgroundTasks, settings: SettingsDep
) -> Course:
    course = course_service.create_course(db, data)
    message = f"course created: {course.title}"                  # homework answer (Video 21)
    background_tasks.add_task(write_log, message, settings.log_file)
    return course


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_api_key), Depends(require_admin)],
)
def delete_course(course: CourseDep, db: DBSession) -> None:
    course_service.delete_course(db, course)
