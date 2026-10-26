# Homework answer from Video 13 - CourseIn / CourseOut
# Run:  fastapi dev homework_video13.py
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(title="Courses - Homework 13")


class CourseIn(BaseModel):
    title: str = Field(min_length=3)
    price: float = Field(ge=0)
    internal_notes: str | None = None      # stored, but NEVER returned


class CourseOut(BaseModel):
    id: int
    title: str
    price: float


class CourseInDB(CourseOut):
    internal_notes: str | None = None


COURSES: dict[int, CourseInDB] = {}


@app.post("/courses", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(course: CourseIn) -> CourseInDB:
    new_id = max(COURSES, default=0) + 1
    COURSES[new_id] = CourseInDB(id=new_id, **course.model_dump())
    return COURSES[new_id]


@app.get("/courses", response_model=list[CourseOut])
def list_courses() -> list[CourseInDB]:
    return list(COURSES.values())


@app.delete(
    "/courses/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"description": "Course not found"}},
)
def delete_course(course_id: int) -> None:
    if COURSES.pop(course_id, None) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
