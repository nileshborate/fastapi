# Routers = the HTTP layer. Shared logic comes from dependencies.
from fastapi import APIRouter, Depends, status

from app.dependencies import CourseDep, Filters, Pagination, allow_staff, require_admin, verify_api_key
from app.schemas.course import CourseCreate, CourseOut
from app.services import course_service

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("")
def list_courses(page: Pagination, filters: Filters) -> list[CourseOut]:
    return course_service.list_courses(page.skip, page.limit, filters.min_price, filters.max_price)


@router.get("/{course_id}")
def get_course(course: CourseDep) -> CourseOut:
    return course


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_api_key), Depends(allow_staff)],
)
def create_course(data: CourseCreate) -> CourseOut:
    return course_service.create_course(data)


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_api_key), Depends(require_admin)],
)
def delete_course(course: CourseDep) -> None:
    course_service.delete_course(course.id)
