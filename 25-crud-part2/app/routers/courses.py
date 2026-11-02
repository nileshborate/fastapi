# Routers = the HTTP layer. Shared logic comes from dependencies.
from fastapi import APIRouter, BackgroundTasks, Depends, Response, status

from app.dependencies import (
    CourseDep, DBSession, Filters, Pagination, SettingsDep, Sort,
    allow_staff, require_admin, verify_api_key,
)
from app.models import Course
from app.schemas.course import CourseCreate, CourseOut, CourseUpdate
from app.services import course_service
from app.tasks import write_log

router = APIRouter(prefix="/courses", tags=["Courses"])


# The functions return database objects (Course).  response_model = the shape the client gets.
@router.get("", response_model=list[CourseOut])
def list_courses(
    db: DBSession, page: Pagination, filters: Filters, sort: Sort, response: Response
) -> list[Course]:
    total = course_service.count_matching(db, filters.min_price, filters.max_price, filters.q)
    response.headers["X-Total-Count"] = str(total)              # NEW: how many match, in ALL pages
    return course_service.list_courses(
        db, page.skip, page.limit,
        filters.min_price, filters.max_price, filters.q,
        sort.sort_by, sort.order,
    )


@router.get("/by-title/{title}", response_model=CourseOut)       # homework answer (Video 24)
def get_course_by_title(title: str, db: DBSession) -> Course:
    return course_service.get_course_by_title(db, title)


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


@router.put(                                                     # NEW: replace the WHOLE course
    "/{course_id}",
    response_model=CourseOut,
    dependencies=[Depends(verify_api_key), Depends(allow_staff)],
)
def replace_course(course: CourseDep, data: CourseCreate, db: DBSession) -> Course:
    return course_service.update_course(db, course, data.model_dump())


@router.patch(                                                   # NEW: change only SOME fields
    "/{course_id}",
    response_model=CourseOut,
    dependencies=[Depends(verify_api_key), Depends(allow_staff)],
)
def update_course(course: CourseDep, data: CourseUpdate, db: DBSession) -> Course:
    changes = data.model_dump(exclude_unset=True)               # ONLY the fields the client sent
    return course_service.update_course(db, course, changes)


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_api_key), Depends(require_admin)],
)
def delete_course(course: CourseDep, db: DBSession) -> None:
    course_service.delete_course(db, course)
