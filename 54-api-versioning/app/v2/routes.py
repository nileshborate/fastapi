from fastapi import APIRouter, HTTPException, status

from app import store
from app.v2.schemas import CourseInV2, CourseV2

router = APIRouter(prefix="/courses", tags=["Courses v2"])


@router.get("")
def list_courses() -> list[CourseV2]:
    return [CourseV2.from_record(r) for r in store.COURSES.values()]


@router.get("/{course_id}")
def read_course(course_id: int) -> CourseV2:
    record = store.get_course(course_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return CourseV2.from_record(record)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_course(data: CourseInV2) -> CourseV2:
    paise = int(data.price.amount * 100)
    record = store.add_course(data.title, data.teacher.name, paise, data.tags)
    return CourseV2.from_record(record)
