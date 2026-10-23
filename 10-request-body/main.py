# Video 10 - Request Body with Pydantic
# Run:  fastapi dev main.py     ->  http://127.0.0.1:8000/docs
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel

app = FastAPI(title="Course Hub API", version="1.3.0")


# 1. A Pydantic model describes the JSON body we expect
class CourseCreate(BaseModel):
    title: str                      # required (no default)
    level: str = "beginner"         # optional (has a default)
    price: int = 0
    published: bool = False
    description: str | None = None


class Review(BaseModel):
    student: str
    rating: int
    comment: str | None = None


COURSES: list[dict[str, Any]] = [
    {"id": 1, "title": "FastAPI Basics", "level": "beginner", "price": 0, "published": True, "description": None},
    {"id": 2, "title": "Pydantic Models", "level": "beginner", "price": 499, "published": True, "description": None},
    {"id": 3, "title": "Databases with SQLAlchemy", "level": "intermediate", "price": 999, "published": True, "description": None},
]


def next_id() -> int:
    return max((course["id"] for course in COURSES), default=0) + 1


@app.get("/courses")
def list_courses() -> list[dict[str, Any]]:
    return COURSES


# 2. POST: create a new course from the request body
@app.post("/courses", status_code=201)
def create_course(course: CourseCreate) -> dict[str, Any]:
    new_course = {"id": next_id(), **course.model_dump()}
    COURSES.append(new_course)
    return new_course


# 3. PUT: replace a whole course (path parameter + body)
@app.put("/courses/{course_id}")
def replace_course(
    course_id: Annotated[int, Path(gt=0)],
    course: CourseCreate,
) -> dict[str, Any]:
    for index, existing in enumerate(COURSES):
        if existing["id"] == course_id:
            updated = {"id": course_id, **course.model_dump()}
            COURSES[index] = updated
            return updated
    raise HTTPException(status_code=404, detail="Course not found")


# 4. Path + body + query in one endpoint
@app.post("/courses/{course_id}/reviews", status_code=201)
def add_review(
    course_id: Annotated[int, Path(gt=0)],
    review: Review,
    notify: bool = False,
) -> dict[str, Any]:
    return {"course_id": course_id, "review": review.model_dump(), "notify": notify}
