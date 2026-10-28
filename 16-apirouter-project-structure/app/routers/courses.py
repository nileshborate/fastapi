# Routers = the HTTP layer: URLs, methods, status codes
from fastapi import APIRouter, HTTPException, status

from app.schemas.course import CourseCreate, CourseOut
from app.services import course_service

router = APIRouter(
    prefix="/courses",
    tags=["Courses"],
    responses={404: {"description": "Course not found"}},
)


@router.get("")
def list_courses() -> list[CourseOut]:
    return course_service.list_courses()


@router.get("/{course_id}")
def get_course(course_id: int) -> CourseOut:
    course = course_service.get_course(course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


@router.post("", status_code=status.HTTP_201_CREATED)
def create_course(data: CourseCreate) -> CourseOut:
    return course_service.create_course(data)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: int) -> None:
    if not course_service.delete_course(course_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
