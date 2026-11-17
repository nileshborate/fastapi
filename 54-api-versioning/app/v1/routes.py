from fastapi import APIRouter, HTTPException, status

from app import store
from app.v1.schemas import CourseInV1, CourseV1

router = APIRouter(prefix="/courses", tags=["Courses v1"])


@router.get("")
def list_courses() -> list[CourseV1]:
    return [CourseV1.from_record(r) for r in store.COURSES.values()]


@router.get("/{course_id}")
def read_course(course_id: int) -> CourseV1:
    record = store.get_course(course_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return CourseV1.from_record(record)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_course(data: CourseInV1) -> CourseV1:
    record = store.add_course(data.name, data.teacher, data.price * 100, tags=[])
    return CourseV1.from_record(record)
